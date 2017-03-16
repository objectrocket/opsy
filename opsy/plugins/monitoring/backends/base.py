import asyncio
import uuid
from datetime import datetime
import aiohttp
from flask import abort
import opsy
from opsy.models import TimeStampMixin, OpsyQuery, NamedResource, BaseResource
from opsy.flask_extensions import db
from opsy.plugins.monitoring.dashboard import Dashboard
from opsy.plugins.monitoring.backends import async_task
from opsy.plugins.monitoring.exceptions import PollFailure, BackendNotFound
from sqlalchemy.orm import synonym
from stevedore import driver
from stevedore.exception import NoMatches


class CacheQuery(OpsyQuery):

    def wtfilter_by(self, dashboard=None, **kwargs):
        filters = []
        if dashboard:
            try:
                dashboard = Dashboard.query.filter_by(
                    name=dashboard).first_or_fail()
                filters = dashboard.get_filters_list(
                    self._joinpoint_zero().class_)
            except ValueError:
                abort(400, 'Dashboard %s does not exist' % dashboard)
        return super().wtfilter_by(**kwargs).filter(*filters)


class BaseCache(BaseResource):

    query_class = CacheQuery

    backend = db.Column(db.String(20))
    last_poll_time = db.Column(db.DateTime, default=None)

    __mapper_args__ = {
        'polymorphic_on': backend,
        'polymorphic_identity': 'base'
    }


class BaseEntity(BaseCache):

    entity = None
    zone_id = db.Column(db.String(36))
    zone_name = db.Column(db.String(64))
    query_class = OpsyQuery
    last_poll_time = db.Column(db.DateTime, default=datetime.utcnow())
    extra = db.Column(db.Text)

    @property
    def dict_extra_out(self):
        event_dict = self.dict_out
        event_dict['extra'] = self.extra
        return event_dict

    def get_dict(self, extra=False, **kwargs):
        if extra:
            return self.dict_extra_out
        else:
            return self.dict_out

    @classmethod
    def filter_api_response(cls, response):
        return response


class Client(BaseEntity, db.Model):

    entity = 'clients'
    __tablename__ = 'monitoring_clients'

    class ClientQuery(CacheQuery):

        def all_dict_out(self, extra=False, **kwargs):
            clients_silences = self.outerjoin(Silence, db.and_(
                Client.zone_name == Silence.zone_name,
                Client.name == Silence.client_name,
                Silence.silence_type == 'client')).add_entity(Silence).all()
            clients_json = []
            for client, silence in clients_silences:
                if extra:
                    client_json = client.dict_extra_out
                else:
                    client_json = client.dict_out
                client_json['silenced'] = bool(silence)
                clients_json.append(client_json)
            return clients_json

    query_class = ClientQuery

    name = db.Column(db.String(128))
    updated_at = db.Column(db.DateTime)
    version = db.Column(db.String(128))
    address = db.Column(db.String(128))

    events = db.relationship('Event', backref='client', lazy='joined',
                             query_class=OpsyQuery, primaryjoin="and_("
                             "Client.zone_id==foreign(Event.zone_id), "
                             "Client.name==foreign(Event.client_name))")

    results = db.relationship('Result', backref='client', lazy='joined',
                              query_class=OpsyQuery, primaryjoin="and_("
                              "Client.zone_id==foreign(Result.zone_id), "
                              "Client.name==foreign(Result.client_name))")

    silences = db.relationship('Silence', backref='client', lazy='joined',
                               query_class=OpsyQuery, primaryjoin="and_("
                               "Client.zone_id == foreign("
                               "Silence.zone_id), "
                               "Client.name == foreign(Silence.client_name))")

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_id'], ['monitoring_zones.id'],
                                ondelete='CASCADE'),
        db.UniqueConstraint('zone_id', 'name', name='client_uc'),
    )

    def __init__(self, zone, extra):
        self.id = str(uuid.uuid3(  # pylint: disable=invalid-name
            uuid.UUID(self.zone_id), self.name))

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('client', cls.name))

    @property
    def status(self):
        results = self.results.all()
        if all([True if (x.status == 'ok') else False for x in results]):
            return 'ok'
        elif any([True if (x.status == 'critical') else False
                  for x in results]):
            return 'critical'
        else:
            return 'warning'

    @property
    def silenced(self):
        return bool(self.silences.filter(Silence.silence_type == 'client').first())

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'zone_name': self.zone_name,
            'backend': self.backend,
            'updated_at': self.updated_at,
            'version': self.version,
            'address': self.address,
            'last_poll_time': self.last_poll_time,
            'name': self.name
        }

    def __repr__(self):
        return '<%s %s/%s>' % (self.__class__.__name__, self.zone_name,
                               self.name)


class Check(BaseEntity, db.Model):

    entity = 'checks'
    __tablename__ = 'monitoring_checks'

    name = db.Column(db.String(128))
    occurrences_threshold = db.Column(db.BigInteger)
    interval = db.Column(db.BigInteger)
    command = db.Column(db.Text)

    results = db.relationship('Result', backref='check', lazy='dynamic',
                              query_class=OpsyQuery,
                              primaryjoin="and_("
                              "Check.zone_id==foreign(Result.zone_id), "
                              "Check.name==foreign(Result.check_name))")
    events = db.relationship('Event', backref='check', lazy='dynamic',
                             query_class=OpsyQuery,
                             primaryjoin="and_("
                             "Check.zone_id==foreign(Event.zone_id), "
                             "Check.name==foreign(Event.check_name))")

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_id'], ['monitoring_zones.id'],
                                ondelete='CASCADE'),
        db.UniqueConstraint('zone_id', 'name', name='check_uc'),
    )

    def __init__(self, zone, extra):
        self.id = str(uuid.uuid3(  # pylint: disable=invalid-name
            uuid.UUID(self.zone_id), self.name))

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('check', cls.name))

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'zone_name': self.zone_name,
            'backend': self.backend,
            'last_poll_time': self.last_poll_time,
            'name': self.name,
            'occurrences_threshold': self.occurrences_threshold,
            'interval': self.interval,
            'command': self.command
        }

    def __repr__(self):
        return '<%s %s/%s>' % (self.__class__.__name__, self.zone_name,
                               self.name)


class Result(BaseEntity, db.Model):

    entity = 'results'
    __tablename__ = 'monitoring_results'

    class ResultQuery(CacheQuery):

        def all_dict_out(self, extra=False, **kwargs):
            clients_silences = self.outerjoin(Silence, db.and_(
                Result.zone_name == Silence.zone_name,
                Result.client_name == Silence.client_name,
                Result.check_name == Silence.check_name)).add_entity(
                    Silence).all()
            events_json = []
            for event, silence in clients_silences:
                if extra:
                    event_json = event.dict_extra_out
                else:
                    event_json = event.dict_out
                event_json['silenced'] = bool(silence)
                events_json.append(event_json)
            return events_json

    query_class = ResultQuery

    client_name = db.Column(db.String(128))
    check_name = db.Column(db.String(128))
    occurrences_threshold = db.Column(db.BigInteger)
    status = db.Column(db.String(16))
    interval = db.Column(db.BigInteger)
    command = db.Column(db.Text)
    output = db.Column(db.Text)

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_id'], ['monitoring_zones.id'],
                                ondelete='CASCADE'),
        db.UniqueConstraint('zone_id', 'client_name', 'check_name',
                            name='result_uc'),
        db.CheckConstraint(status.in_(
            ['ok', 'warning', 'critical', 'unknown']))
    )

    def __init__(self, zone, extra):
        self.id = str(uuid.uuid3(  # pylint: disable=invalid-name
            uuid.UUID(self.zone_id), self.client_name + self.check_name))

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('check', cls.check_name),
                ('client', cls.client_name))

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'zone_name': self.zone_name,
            'backend': self.backend,
            'last_poll_time': self.last_poll_time,
            'client_name': self.client_name,
            'check_name': self.check_name,
            'occurrences_threshold': self.occurrences_threshold,
            'status': self.status,
            'interval': self.interval,
            'command': self.command,
            'output': self.output
        }

    def __repr__(self):
        return '<%s %s/%s/%s>' % (self.__class__.__name__, self.zone_name,
                                  self.client_name, self.check_name)


class Event(BaseEntity, db.Model):

    entity = 'events'
    __tablename__ = 'monitoring_events'

    class EventQuery(CacheQuery):

        def wtfilter_by(self, hide_silenced=None, **kwargs):
            filters = []
            if hide_silenced:
                hide_silenced = hide_silenced.split(',')
                if 'checks' in hide_silenced:
                    filters.append(db.not_(Event.silences.any(
                        client_name=Event.client_name,
                        check_name=Event.check_name)))
                if 'clients' in hide_silenced:
                    filters.append(db.not_(Client.silences.any(
                        client_name=Event.client_name, silence_type='client')))
                if 'occurrences' in hide_silenced:
                    filters.append(db.not_(
                        Event.occurrences < Event.occurrences_threshold))
            return super().wtfilter_by(**kwargs).filter(*filters)

        def all_dict_out(self, extra=False, **kwargs):
            clients_silences = self.outerjoin(Silence, db.and_(
                Event.zone_name == Silence.zone_name,
                db.or_(
                    db.and_(
                        Event.client_name == Silence.client_name,
                        Silence.check_name == Event.check_name,
                        Silence.silence_type == 'check'),
                    db.and_(
                        Event.client_name == Silence.client_name,
                        Silence.silence_type == 'client')
                ))).add_entity(Silence).all()
            events_json = []
            for event, silence in clients_silences:
                if extra:
                    event_json = event.dict_extra_out
                else:
                    event_json = event.dict_out
                event_json['silenced'] = bool(silence)
                events_json.append(event_json)
            return events_json

        def count_checks(self):
            check_count = {x: y for x, y in self.with_entities(
                Event.check_name, db.func.count(Event.check_name)).group_by(
                    Event.check_name).order_by(db.desc(db.func.count(
                        Event.check_name))).all()}
            return sorted([{'name': x, 'count': y} for x, y in
                           check_count.items()],
                          key=lambda x: (-x['count'], x['name']))

    query_class = EventQuery

    client_name = db.Column(db.String(128))
    check_name = db.Column(db.String(128))
    updated_at = db.Column(db.DateTime)
    occurrences_threshold = db.Column(db.BigInteger)
    occurrences = db.Column(db.BigInteger)
    status = db.Column(db.String(16))
    command = db.Column(db.Text)
    interval = db.Column(db.BigInteger)
    output = db.Column(db.Text)

    silences = db.relationship('Silence', backref='events', lazy='dynamic',
                               query_class=OpsyQuery,
                               primaryjoin="and_("
                               "Event.zone_id==foreign(Silence.zone_id),"
                               "Event.client_name==foreign("
                               "Silence.client_name), "
                               "Event.check_name==foreign("
                               "Silence.check_name))")

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_id'], ['monitoring_zones.id'],
                                ondelete='CASCADE'),
        db.UniqueConstraint('zone_id', 'client_name', 'check_name',
                            name='event_uc'),
        db.CheckConstraint(status.in_(
            ['ok', 'warning', 'critical', 'unknown']))
    )

    def __init__(self, zone, extra):
        self.id = str(uuid.uuid3(  # pylint: disable=invalid-name
            uuid.UUID(self.zone_id), self.client_name + self.check_name))

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('check', cls.check_name),
                ('client', cls.client_name))

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'backend': self.backend,
            'zone_name': self.zone_name,
            'last_poll_time': self.last_poll_time,
            'client_name': self.client_name,
            'check_name': self.check_name,
            'updated_at': self.updated_at,
            'occurrences_threshold': self.occurrences_threshold,
            'occurrences': self.occurrences,
            'status': self.status,
            'interval': self.interval,
            'command': self.command,
            'output': self.output,
        }

    def __repr__(self):
        return '<%s %s/%s/%s>' % (self.__class__.__name__, self.zone_name,
                                  self.client_name, self.check_name)


class Silence(BaseEntity, db.Model):

    entity = 'silences'
    __tablename__ = 'monitoring_silences'

    client_name = db.Column(db.String(128))
    check_name = db.Column(db.String(128))
    silence_type = db.Column(db.String(16))
    created_at = db.Column(db.DateTime)
    expire_at = db.Column(db.DateTime)
    comment = db.Column(db.Text)

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_id'], ['monitoring_zones.id'],
                                ondelete='CASCADE'),
        db.UniqueConstraint('zone_id', 'client_name', 'check_name',
                            'silence_type', name='silence_uc'),
        db.CheckConstraint(silence_type.in_(
            ['client', 'check']))
    )

    def __init__(self, zone, extra):
        check_name = self.check_name or ''
        self.id = str(uuid.uuid3(  # pylint: disable=invalid-name
            uuid.UUID(self.zone_id), self.silence_type + self.client_name + check_name))

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('check', cls.check_name),
                ('client', cls.client_name))

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'zone_name': self.zone_name,
            'backend': self.backend,
            'last_poll_time': self.last_poll_time,
            'client_name': self.client_name,
            'check_name': self.check_name,
            'silence_type': self.silence_type,
            'created_at': self.created_at,
            'expire_at': self.expire_at,
            'comment': self.comment
        }

    def __repr__(self):
        return '<%s %s/%s/%s>' % (self.__class__.__name__, self.zone_name,
                                  self.client_name, self.check_name)


class Zone(BaseCache, NamedResource, TimeStampMixin, db.Model):

    entity = 'zones'
    __tablename__ = 'monitoring_zones'

    models = [Check, Client, Event, Silence, Result]

    _enabled = db.Column('enabled', db.Boolean(), default=0)
    _status = db.Column('status', db.String(64))
    status_message = db.Column(db.String(64))
    host = db.Column(db.String(64))
    path = db.Column(db.String(64))
    protocol = db.Column(db.String(64))
    port = db.Column(db.Integer())
    timeout = db.Column(db.Integer())
    interval = db.Column(db.Integer())
    username = db.Column(db.String(64))
    password = db.Column(db.String(64))
    verify_ssl = db.Column(db.Boolean())

    clients = db.relationship('Client', backref='zone', lazy='dynamic',
                              query_class=OpsyQuery)
    checks = db.relationship('Check', backref='zone', lazy='dynamic',
                             query_class=OpsyQuery)
    events = db.relationship('Event', backref='zone', lazy='dynamic',
                             query_class=OpsyQuery)
    results = db.relationship('Result', backref='zone', lazy='dynamic',
                              query_class=OpsyQuery)
    silences = db.relationship('Silence', backref='zone', lazy='dynamic',
                               query_class=OpsyQuery)

    def __init__(self, name, enabled=0, host=None, path=None, protocol='http',
                 port=80, timeout=30, interval=30, username=None, password=None,
                 verify_ssl=True, **kwargs):
        self.name = name
        self.enabled = enabled
        if self.enabled:
            self.status = 'new'
        else:
            self.status = 'disabled'
        self.host = host
        self.path = path
        self.protocol = protocol
        self.port = port
        self.timeout = timeout
        self.interval = interval
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl

    @classmethod
    def create(cls, name, backend, **kwargs):
        try:
            backend_class = driver.DriverManager(
                namespace='opsy.monitoring.backend',
                name=backend,
                invoke_on_load=False).driver
        except NoMatches:
            raise BackendNotFound('Unable to load backend "%s"' % backend)
        return super().create(name, obj_class=backend_class, **kwargs)

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.name),)

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        status_map = {
            'new': 'This zone is new and has not polled yet.',
            'disabled': 'This zone is disabled.',
            'ok': 'Last poll successful.',
            'warning': 'Last poll encountered problems.',
            'critical': 'Last poll failed.',
        }
        self._status = value
        self.status_message = status_map.get(value)

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if int(value) == 0:
            self._enabled = 0
            self.status = 'disabled'
        if int(value) == 1:
            self._enabled = 1
            self.status = 'new'

    enabled = synonym('_enabled', descriptor=enabled)

    @asyncio.coroutine
    def update_objects(self, app, model):
        raise NotImplementedError

    def get_update_tasks(self, app):
        tasks = []
        for model in self.models:
            tasks.append(async_task(self.update_objects(app, model)))
        return tasks

    @classmethod
    def purge_cache(cls, zone_name, app):
        for model in cls.models:
            app.logger.info('Purging %s cache for %s' % (
                model.__tablename__, zone_name))
            model.query.filter(model.zone_name == zone_name).delete()

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'name': self.name,
            'backend': self.backend,
            'status': self.status,
            'status_message': self.status_message,
            'last_poll_time': self.last_poll_time,
            'host': self.host,
            'path': self.path,
            'protocol': self.protocol,
            'port': self.port,
            'timeout': self.timeout,
            'interval': self.interval
        }

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)


class HttpZoneMixin(object):

    @property
    def base_url(self):
        if self.path:
            url = '%s://%s:%s/%s' % (self.protocol, self.host, self.port,
                                     self.path.strip('/'))
        else:
            url = '%s://%s:%s' % (self.protocol, self.host, self.port)
        return url

    def _create_session(self):
        auth = aiohttp.BasicAuth(self.username, self.password) \
            if (self.username and self.password) else None
        conn = aiohttp.TCPConnector(verify_ssl=False) \
            if not self.verify_ssl else None
        headers = {'User-Agent': 'Opsy/%s' % opsy.__version__}
        return aiohttp.ClientSession(auth=auth, connector=conn,
                                     headers=headers)

    @asyncio.coroutine
    def get(self, session, url, expected_status=None):
        expected_status = expected_status or [200]
        try:
            with aiohttp.Timeout(self.timeout):
                response = yield from session.get(url)
        except asyncio.TimeoutError:
            raise aiohttp.errors.ClientError('Timeout exceeded')
        if response.status not in expected_status:
            response.close()
            raise aiohttp.errors.ClientError('Unexpected response from %s, got'
                                             ' %s' % (url, response.status))
        return (yield from response.json())

    @asyncio.coroutine
    def update_objects(self, app, model):
        del_objects = []
        init_objects = []
        results = []
        url = '%s/%s' % (self.base_url, model.uri)
        try:
            with self._create_session() as session:
                app.logger.debug('Making request to %s' % url)
                response = yield from self.get(session, url)
                results = model.filter_api_response(response)
        except aiohttp.errors.ClientError as exc:
            message = 'Error updating %s cache for %s: %s' % (
                model.entity, self.name, exc)
            app.logger.error(message)
            raise PollFailure(message)
        del_objects = [model.query.filter(model.zone_id == self.id)]
        for result in results:
            init_objects.append(model(self, result))
        app.logger.info('Updated %s cache for %s' % (
            model.entity, self.name))
        return del_objects, init_objects
