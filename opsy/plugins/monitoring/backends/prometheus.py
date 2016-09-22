import aiohttp
import asyncio
import dateutil.parser
from flask import json
from time import time
from opsy.plugins.monitoring.backends.base import (Client, Result, Event,
                                                   Silence, Zone, HttpZoneMixin)
from opsy.plugins.monitoring.backends import async_task


class PrometheusBase(object):
    __mapper_args__ = {
        'polymorphic_identity': 'prometheus'
    }


class PrometheusClient(PrometheusBase, Client):

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.name = extra['labels']['instance']
        try:
            self.updated_at = dateutil.parser.parse(
                extra['annotations']['activeSince'])
        except TypeError:
            self.updated_at = None
        self.version = None
        self.address = None
        self.extra = json.dumps(extra)


class PrometheusResult(PrometheusBase, Result):

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.client_name = extra['labels']['instance']
        self.check_name = extra['labels']['alertname']
        status_map = ['ok', 'warning', 'critical']
        try:
            self.status = status_map[int(extra['annotations']['value'])]
        except IndexError:
            self.status = 'unknown'
        self.occurrences_threshold = None
        self.command = extra['annotations']['alertingRule']
        self.output = extra['annotations']['description']
        self.interval = None
        self.extra = json.dumps(extra)


class PrometheusEvent(PrometheusBase, Event):

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.client_name = extra['labels']['instance']
        self.check_name = extra['labels']['alertname']
        try:
            self.updated_at = dateutil.parser.parse(
                extra['annotations']['activeSince'])
        except TypeError:
            self.updated_at = None
        self.occurrences_threshold = None
        self.occurrences = None
        status_map = ['ok', 'warning', 'critical']
        try:
            self.status = status_map[int(extra['annotations']['value'])]
        except IndexError:
            self.status = 'unknown'
        self.command = extra['annotations']['alertingRule']
        self.output = extra['annotations']['description']
        self.interval = None
        self.extra = json.dumps(extra)


class PrometheusSilence(PrometheusBase, Silence):

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        path_list = extra['path'].split('/')
        self.client_name = path_list[1]
        try:
            self.check_name = path_list[2]
        except IndexError:
            self.check_name = None
        self.comment = json.dumps(extra['content'])
        if extra['content'].get('timestamp'):
            self.created_at = datetime.utcfromtimestamp(
                int(extra['content']['timestamp']))
        if extra['expire'] == -1:
            self.expire_at = None
        else:
            self.expire_at = datetime.utcfromtimestamp(
                int(time() + int(extra['expire'])))
        self.extra = json.dumps(extra)


class PrometheusZone(PrometheusBase, HttpZoneMixin, Zone):  # pylint: disable=abstract-method

    models = [PrometheusClient, PrometheusEvent, PrometheusSilence,
              PrometheusResult]

    def __init__(self, name, host=None, path='/api/v1', protocol='http', port=9093,  # pylint: disable=too-many-arguments
                 timeout=30, interval=30, username=None, password=None,
                 verify_ssl=True, **kwargs):
        super().__init__(name, host=host, path=path, protocol=protocol,
                         port=port, timeout=timeout, interval=interval,
                         username=username, password=password,
                         verify_ssl=verify_ssl, **kwargs)

    def get_update_tasks(self, app):
        return [async_task(self.update_objects(app))]

    @asyncio.coroutine
    def get(self, session, url):
        with aiohttp.Timeout(self.timeout):
            response = yield from session.get(url)
            return (yield from response.json())

    @asyncio.coroutine
    def update_objects(self, app):
        init_objects = []
        del_objects = []
        results = []
        url = '%s/alerts' % self.base_url
        try:
            with self._create_session() as session:
                app.logger.debug('Making request to %s' % url)
                results = yield from self.get(session, url)
        except aiohttp.errors.ClientError as exc:
            for model in self.models:
                message = 'Error updating %s cache for %s: %s' % (
                    model.__tablename__, self.name, exc)
                app.logger.error(message)
                init_objects.extend(model.update_last_poll(
                    self.name, 'critical', message))
            return del_objects, init_objects
        for model in self.models:
            del_objects.append(
                model.query.filter(model.zone_name == self.name))
            init_objects.extend(model.update_last_poll(
                self.name, 'ok', 'Success'))
        clients_name = []
        for result in results['data']:
            if result['labels']['instance'] not in clients_name:
                init_objects.append(PrometheusClient(self.name, result))
                clients_name.append(result['labels']['instance'])
            init_objects.append(PrometheusEvent(self.name, result))
            init_objects.append(PrometheusResult(self.name, result))
            # if result.get('problemAcked') != 0 or \
            #    result.get('notificationsEnabled') != 1 or \
            #    result.get('scheduledDowntime') != 0:
            #     init_objects.append(PrometheusSilence(self.name, result))
        app.logger.info('Updated cache for %s' % self.name)
        return del_objects, init_objects
