import asyncio
import uuid
from collections import OrderedDict
import aiohttp
from flask import abort
from sqlalchemy.orm import synonym
from stevedore import driver
from stevedore.exception import NoMatches
import opsy
from opsy.models import TimeStampMixin, OpsyQuery, NamedResource, BaseResource
from opsy.flask_extensions import db
from opsy.plugins.monitoring.dashboard import Dashboard
from opsy.plugins.monitoring.exceptions import PollFailure, BackendNotFound


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

    __mapper_args__ = {
        'polymorphic_on': backend,
        'polymorphic_identity': 'base'
    }


class BaseEntity(BaseCache):

    entity = None
    zone_id = db.Column(db.String(36))
    zone_name = db.Column(db.String(64))
    query_class = OpsyQuery
    raw_info = db.Column(db.JSON)


class Client(BaseEntity, db.Model):

    entity = 'clients'
    __tablename__ = 'monitoring_clients'

    class ClientQuery(CacheQuery):

        def all_dict_out(self, **kwargs):
            clients_silences = self.outerjoin(Silence, db.and_(
                Client.zone_name == Silence.zone_name,
                Client.name == Silence.client_name,
                Silence.check_name is None)).add_entity(Silence).all()
            clients_json = []
            for client, silence in clients_silences:
                client_json = client.dict_out
                client_json['silenced'] = bool(silence)
                clients_json.append(client_json)
            return clients_json

    query_class = ClientQuery

    name = db.Column(db.String(128))
    subscriptions = db.Column(db.JSON)
    updated_at = db.Column(db.DateTime)

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
                               "Client.zone_id == foreign(Silence.zone_id), "
                               "Client.name == foreign(Silence.client_name))")

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_id'], ['monitoring_zones.id'],
                                ondelete='CASCADE'),
        db.UniqueConstraint('zone_id', 'name', name='client_uc'),
    )

    def __init__(self, zone, raw_info):
        self.id = str(uuid.uuid3(  # pylint: disable=invalid-name
            uuid.UUID(self.zone_id), self.name))
        self.raw_info = raw_info

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
        return 'warning'

    @property
    def dict_out(self):
        return OrderedDict([
            ('id', self.id),
            ('zone_name', self.zone_name),
            ('zone_id', self.zone_id),
            ('backend', self.backend),
            ('updated_at', self.updated_at),
            ('last_poll_time', self.zone.last_poll_time),
            ('name', self.name),
            ('subscriptions', self.subscriptions),
            ('silences', [x.get_dict() for x in self.silences])
        ])

    def __repr__(self):
        return '<%s %s/%s>' % (self.__class__.__name__, self.zone_name,
                               self.name)


class Check(BaseEntity, db.Model):

    entity = 'checks'
    __tablename__ = 'monitoring_checks'

    name = db.Column(db.String(128))
    subscribers = db.Column(db.JSON)
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

    def __init__(self, zone, raw_info):
        self.id = str(uuid.uuid3(  # pylint: disable=invalid-name
            uuid.UUID(self.zone_id), self.name))
        self.raw_info = raw_info

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('check', cls.name))

    @property
    def dict_out(self):
        return OrderedDict([
            ('id', self.id),
            ('zone_name', self.zone_name),
            ('zone_id', self.zone_id),
            ('backend', self.backend),
            ('last_poll_time', self.zone.last_poll_time),
            ('name', self.name),
            ('subscribers', self.subscribers),
            ('occurrences_threshold', self.occurrences_threshold),
            ('interval', self.interval),
            ('command', self.command)
        ])

    def __repr__(self):
        return '<%s %s/%s>' % (self.__class__.__name__, self.zone_name,
                               self.name)


class Result(BaseEntity, db.Model):

    entity = 'results'
    __tablename__ = 'monitoring_results'

    client_name = db.Column(db.String(128))
    check_name = db.Column(db.String(128))
    check_subscribers = db.Column(db.JSON)
    updated_at = db.Column(db.DateTime)
    occurrences_threshold = db.Column(db.BigInteger)
    status = db.Column(db.String(16))
    interval = db.Column(db.BigInteger)
    command = db.Column(db.Text)
    output = db.Column(db.Text)

    silences = db.relationship(
        'Silence', backref='results', lazy='joined', primaryjoin='''and_(
        Result.zone_name == foreign(Silence.zone_name),
        or_(
            and_(  # This check on this client is silenced
                Result.client_name == foreign(Silence.client_name),
                Result.check_name == foreign(Silence.check_name),
                foreign(Silence.subscription) == None
                ),
            and_(  # This client is silenced
                Result.client_name == foreign(Silence.client_name),
                foreign(Silence.check_name) == None,
                foreign(Silence.subscription) == None
                ),
            and_(  # This check is silenced
                Result.check_name == foreign(Silence.check_name),
                foreign(Silence.client_name) == None,
                foreign(Silence.subscription) == None
                ),
            and_(  # This check on this subscription is silenced
                Result.check_name == Silence.check_name,
                foreign(Silence.client_name) == None,
                func.json_contains(
                    Result.check_subscribers,
                    func.concat('"', foreign(Silence.subscription), '"')
                    )
                ),
            and_(  # This subscription is silenced
                foreign(Silence.check_name) == None,
                foreign(Silence.client_name) == None,
                func.json_contains(
                    Result.check_subscribers,
                    func.concat('"', foreign(Silence.subscription), '"')
                    )
                )
        ))''')

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_id'], ['monitoring_zones.id'],
                                ondelete='CASCADE'),
        db.UniqueConstraint('zone_id', 'client_name', 'check_name',
                            name='result_uc'),
        db.CheckConstraint(status.in_(
            ['ok', 'warning', 'critical', 'unknown']))
    )

    def __init__(self, zone, raw_info):
        self.id = str(uuid.uuid3(  # pylint: disable=invalid-name
            uuid.UUID(self.zone_id), self.client_name + self.check_name))
        self.raw_info = raw_info

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('check', cls.check_name),
                ('client', cls.client_name))

    @property
    def dict_out(self):
        return OrderedDict([
            ('id', self.id),
            ('zone_name', self.zone_name),
            ('zone_id', self.zone_id),
            ('backend', self.backend),
            ('last_poll_time', self.zone.last_poll_time),
            ('client_name', self.client_name),
            ('check_name', self.check_name),
            ('check_subscribers', self.check_subscribers),
            ('updated_at', self.updated_at),
            ('occurrences_threshold', self.occurrences_threshold),
            ('status', self.status),
            ('interval', self.interval),
            ('command', self.command),
            ('output', self.output),
            ('silences', [x.get_dict() for x in self.silences])
        ])

    def __repr__(self):
        return '<%s %s/%s/%s>' % (self.__class__.__name__, self.zone_name,
                                  self.client_name, self.check_name)


class Event(BaseEntity, db.Model):

    entity = 'events'
    __tablename__ = 'monitoring_events'

    class EventQuery(CacheQuery):

        def wtfilter_by(self, hide=None, client_subscriptions=None,
                        check_subscribers=None, **kwargs):
            filters = []
            if client_subscriptions:
                filters.append(
                    Event.client_subscriptions.contains(client_subscriptions))
            if check_subscribers:
                filters.append(
                    Event.check_subscribers.contains(check_subscribers))
            if hide:
                hide = hide.split(',')
                if 'silenced' in hide:
                    filters.append(db.not_(Event.silences.any()))
                if 'below_occurrences' in hide:
                    filters.append(db.not_(
                        Event.occurrences < Event.occurrences_threshold))
            return super().wtfilter_by(**kwargs).filter(*filters)

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
    client_subscriptions = db.Column(db.JSON)
    check_name = db.Column(db.String(128))
    check_subscribers = db.Column(db.JSON)
    updated_at = db.Column(db.DateTime)
    occurrences_threshold = db.Column(db.BigInteger)
    occurrences = db.Column(db.BigInteger)
    status = db.Column(db.String(16))
    command = db.Column(db.Text)
    interval = db.Column(db.BigInteger)
    output = db.Column(db.Text)

    silences = db.relationship(
        'Silence', backref='events', lazy='joined', primaryjoin='''and_(
        Event.zone_name == foreign(Silence.zone_name),
        or_(
            and_(  # This check on this client is silenced
                Event.client_name == foreign(Silence.client_name),
                Event.check_name == foreign(Silence.check_name),
                foreign(Silence.subscription) == None
                ),
            and_(  # This client is silenced
                Event.client_name == foreign(Silence.client_name),
                foreign(Silence.check_name) == None,
                foreign(Silence.subscription) == None
                ),
            and_(  # This check is silenced
                Event.check_name == foreign(Silence.check_name),
                foreign(Silence.client_name) == None,
                foreign(Silence.subscription) == None
                ),
            and_(  # This check on this subscription is silenced
                Event.check_name == Silence.check_name,
                foreign(Silence.client_name) == None,
                Event.check_subscribers.contains(foreign(Silence.subscription))
                ),
            and_(  # This subscription is silenced
                foreign(Silence.check_name) == None,
                foreign(Silence.client_name) == None,
                Event.client_subscriptions.contains(foreign(Silence.subscription))
                )
        ))''')

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_id'], ['monitoring_zones.id'],
                                ondelete='CASCADE'),
        db.UniqueConstraint('zone_id', 'client_name', 'check_name',
                            name='event_uc'),
        db.CheckConstraint(status.in_(
            ['ok', 'warning', 'critical', 'unknown']))
    )

    def __init__(self, zone, raw_info):
        self.id = str(uuid.uuid3(  # pylint: disable=invalid-name
            uuid.UUID(self.zone_id), self.client_name + self.check_name))
        self.raw_info = raw_info

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('check', cls.check_name),
                ('client', cls.client_name))

    @property
    def dict_out(self):
        return OrderedDict([
            ('id', self.id),
            ('backend', self.backend),
            ('zone_name', self.zone_name),
            ('zone_id', self.zone_id),
            ('last_poll_time', self.zone.last_poll_time),
            ('client_name', self.client_name),
            ('client_subscriptions', self.client_subscriptions),
            ('check_name', self.check_name),
            ('check_subscribers', self.check_subscribers),
            ('updated_at', self.updated_at),
            ('occurrences_threshold', self.occurrences_threshold),
            ('occurrences', self.occurrences),
            ('status', self.status),
            ('interval', self.interval),
            ('command', self.command),
            ('output', self.output),
            ('silences', [x.get_dict() for x in self.silences])
        ])

    def __repr__(self):
        return '<%s %s/%s/%s>' % (self.__class__.__name__, self.zone_name,
                                  self.client_name, self.check_name)


class Silence(BaseEntity, db.Model):

    entity = 'silences'
    __tablename__ = 'monitoring_silences'
    client_name = db.Column(db.String(128))
    check_name = db.Column(db.String(128))
    subscription = db.Column(db.String(128))
    creator = db.Column(db.String(128))
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    expire_at = db.Column(db.DateTime)

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_id'], ['monitoring_zones.id'],
                                ondelete='CASCADE'),
        db.UniqueConstraint('zone_id', 'client_name', 'check_name',
                            'subscription', name='silence_uc')
    )

    def __init__(self, zone, raw_info):
        check_name = self.check_name or ''
        client_name = self.client_name or ''
        subscription = self.subscription or ''
        self.id = str(uuid.uuid3(  # pylint: disable=invalid-name
            uuid.UUID(self.zone_id), subscription + client_name + check_name))
        self.raw_info = raw_info

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('check', cls.check_name),
                ('client', cls.client_name))

    @property
    def dict_out(self):
        return OrderedDict([
            ('id', self.id),
            ('zone_name', self.zone_name),
            ('zone_id', self.zone_id),
            ('backend', self.backend),
            ('last_poll_time', self.zone.last_poll_time),
            ('client_name', self.client_name),
            ('check_name', self.check_name),
            ('subscription', self.subscription),
            ('creator', self.creator),
            ('reason', self.reason),
            ('created_at', self.created_at),
            ('expire_at', self.expire_at)
        ])

    def __repr__(self):
        return '<%s %s/%s/%s>' % (self.__class__.__name__, self.zone_name,
                                  self.client_name, self.check_name)


class Zone(BaseCache, NamedResource, TimeStampMixin, db.Model):

    entity = 'zones'
    __tablename__ = 'monitoring_zones'

    models = [Check, Client, Event, Silence, Result]

    _enabled = db.Column('enabled', db.Boolean(), default=0)
    _status = db.Column('status', db.String(64))
    last_poll_time = db.Column(db.DateTime, default=None)
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

    async def update_objects(self, app, model):
        raise NotImplementedError

    def get_update_tasks(self, app):
        tasks = []
        for model in self.models:
            tasks.append(asyncio.ensure_future(
                self.update_objects(app, model)))
        return tasks

    @classmethod
    def purge_cache(cls, zone_name, app):
        for model in cls.models:
            app.logger.info('Purging %s cache for %s' % (
                model.__tablename__, zone_name))
            model.query.filter(model.zone_name == zone_name).delete()

    @property
    def dict_out(self):
        return OrderedDict([
            ('id', self.id),
            ('name', self.name),
            ('backend', self.backend),
            ('status', self.status),
            ('status_message', self.status_message),
            ('last_poll_time', self.last_poll_time),
            ('host', self.host),
            ('path', self.path),
            ('protocol', self.protocol),
            ('port', self.port),
            ('timeout', self.timeout),
            ('interval', self.interval),
            ('enabled', self.enabled),
            ('created_at', self.created_at),
            ('updated_at', self.updated_at)
        ])

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
        timeout = aiohttp.ClientTimeout(self.timeout)
        return aiohttp.ClientSession(auth=auth, connector=conn,
                                     headers=headers, timeout=timeout)

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

    async def update_objects(self, app, model):
        del_objects = []
        init_objects = []
        results = []
        url = '%s/%s' % (self.base_url, model.uri)
        try:
            async with self._create_session() as session:
                app.logger.debug('Making request to %s' % url)
                results = await self.get(session, url)
        except aiohttp.ClientError as exc:
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
