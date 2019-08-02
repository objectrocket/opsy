import asyncio
from abc import abstractmethod, ABCMeta
import aiohttp
from flask import current_app
from sqlalchemy import and_, tuple_
from werkzeug.urls import url_join
import opsy
from opsy.flask_extensions import db
from opsy.inventory.models import Host
from opsy.monitoring.models import Event
from opsy.monitoring.exceptions import PollFailure


class HttpPollerBackend(metaclass=ABCMeta):

    def __init__(self, monitoring_service, host='localhost', protocol='http',
                 port=80, path='/', interval=60, timeout=30, username=None,
                 password=None, verify_ssl=False):
        self.monitoring_service = monitoring_service
        self.host = host
        self.protocol = protocol
        self.port = port
        self.path = path
        self.interval = interval
        self.timeout = timeout
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl

    @property
    @abstractmethod
    def urls(self):
        """This should return a list of generated URLs to be polled."""

    @abstractmethod
    def decode(self, data):
        """This performs the data decoding. Returns list of raw events."""

    @property
    def base_url(self):
        return url_join(
            f'{self.protocol}://{self.host}:{self.port}', self.path)

    @property
    def config(self):
        """This returns the config for the poller as a dict."""
        return {
            'host': self.host,
            'protocol': self.protocol,
            'port': self.port,
            'path': self.path,
            'interval': self.interval,
            'timeout': self.timeout,
            'username': self.username,
            'password': self.password,
            'verify_ssl': self.verify_ssl
        }

    def _create_session(self):
        auth = aiohttp.BasicAuth(self.username, self.password) \
            if (self.username and self.password) else None
        conn = aiohttp.TCPConnector(verify_ssl=False) \
            if not self.verify_ssl else None
        headers = {'User-Agent': 'Opsy/%s' % opsy.__version__}
        timeout = aiohttp.ClientTimeout(self.timeout)
        return aiohttp.ClientSession(auth=auth, connector=conn,
                                     headers=headers, timeout=timeout)

    async def fetch(self, urls, expected_status=None):
        """This performs the data retrival."""
        async with self._create_session() as session:
            tasks = [
                asyncio.ensure_future(
                    self.get(session, url, expected_status=expected_status))
                for url in urls]
            return await asyncio.gather(*tasks)

    def update(self):
        """This triggers the work needed to update."""
        current_app.logger.info(
            f'Updating monitoring service {self.monitoring_service.name}..')
        try:
            loop = asyncio.get_event_loop()
            data = loop.run_until_complete(self.fetch(self.urls))
        except PollFailure as error:
            current_app.logger.error(  # pylint: disable=no-member
                'Failed to update events on monitoring service %s: %s',
                self.monitoring_service.name, error.__class__.__name__)

        # So basic idea of what we're doing in this next section:
        # 1) We get the list of all events from the API.
        new_events = self.decode(data)
        # 2) We create a key tuple of all the events in a list.
        event_keys = [(self.monitoring_service.id,
                       x['host_name'],
                       x['check_name']) for x in new_events]
        # 3) We get a list of all the hosts with names matching the events.
        hosts = Host.query.filter(
            Host.name.in_([x['host_name'] for x in new_events])).all()
        # 4) We compare this to all unresolved events to find the ones that
        #    resolved since we last polled and mark them as such.
        for resolved_event in Event.query.filter(and_(
                Event.monitoring_service_id == self.monitoring_service.id,
                ~Event.resolved,
                ~tuple_(
                    Event.monitoring_service_id,
                    Event.host_name,
                    Event.check_name).in_(event_keys))).all():
            resolved_event.resolve(commit=False)
            db.session.add(resolved_event)
        # 5) We compare this to all the events we currently know about and mark
        #    those for update so we don't get duplicates. We also add the
        #    host_id if the host exists.
        existing_events = []
        for existing_event in Event.query.filter(and_(
                Event.monitoring_service_id == self.monitoring_service.id,
                ~Event.resolved,
                tuple_(
                    Event.monitoring_service_id,
                    Event.host_name,
                    Event.check_name).in_(event_keys))).all():
            for new_event in new_events:
                if new_event['host_name'] == existing_event.host_name and \
                        new_event['check_name'] == existing_event.check_name:
                    host_id = None
                    for host in hosts:
                        if new_event['host_name'] == host.name:
                            host_id = host.id
                            break
                    existing_events.append(new_event)
                    db.session.add(
                        existing_event.update(commit=False, host_id=host_id,
                                              **new_event))
                    break
        # 6) We eliminate the existing events from the new list.
        new_events = [x for x in new_events if x not in existing_events]
        # 7) We create the new events, adding the host_id if the host exists.
        for new_event in new_events:
            current_app.logger.debug(f'Adding new event: {new_event}')
            host_id = None
            for host in hosts:
                if new_event['host_name'] == host.name:
                    host_id = host.id
                    break
            db.session.add(
                Event(self.monitoring_service, host_id=host_id, **new_event))
        # 8) And commit the changes.
        db.session.commit()
        current_app.logger.info(
            f'Updated monitoring service {self.monitoring_service.name}.')

    async def get(self, session, url, expected_status=None):
        expected_status = expected_status or [200]
        try:
            response = await session.get(url)
        except asyncio.TimeoutError:
            raise aiohttp.ClientError('Timeout exceeded')
        if response.status not in expected_status:
            response.close()
            raise aiohttp.ClientError('Unexpected response from %s, got'
                                      ' %s' % (url, response.status))
        return await response.json()
