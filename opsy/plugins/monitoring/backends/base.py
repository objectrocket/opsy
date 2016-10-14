import asyncio
import aiohttp
from flask_sqlalchemy import BaseQuery
from flask import abort
import uuid
import opsy
from opsy.db import db, TimeStampMixin
from opsy.utils import get_filters_list
from sqlalchemy.orm import synonym
from stevedore import driver
from . import async_task


class DictOut(BaseQuery):

    def all_dict_out(self):
        return [x.dict_out for x in self]

    def all_dict_out_or_404(self):
        dict_list = self.all_dict_out()
        if not dict_list:
            abort(404)
        return dict_list


class ExtraOut(DictOut):

    def all_dict_extra_out(self):
        return [x.dict_extra_out for x in self]

    def all_dict_extra_out_or_404(self):
        dict_list = self.all_dict_extra_out()
        if not dict_list:
            abort(404)
        return dict_list


class BaseCache(object):

    query_class = DictOut

    id = db.Column(db.String(36),  # pylint: disable=invalid-name
                   default=lambda: str(uuid.uuid4()), primary_key=True)
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
    query_class = ExtraOut
    extra = db.Column(db.Text)

    @property
    def dict_extra_out(self):
        event_dict = self.dict_out
        event_dict['extra'] = self.extra
        return event_dict

    @classmethod
    def filter_api_response(cls, response):
        return response


class Client(BaseEntity, db.Model):

    entity = 'clients'
    __tablename__ = 'monitoring_clients'

    class ClientQuery(ExtraOut):

        def all_dict_out(self):
            clients_silences = self.outerjoin(Silence, db.and_(
                Client.zone_name == Silence.zone_name,
                Client.name == Silence.client_name,
                Silence.check_name == '')).add_entity(Silence).all()
            clients_json = []
            for client, silence in clients_silences:
                client_json = client.dict_out
                client_json['silenced'] = bool(silence)
                clients_json.append(client_json)
            return clients_json

    query_class = ClientQuery

    name = db.Column(db.String(128))
    updated_at = db.Column(db.DateTime)
    version = db.Column(db.String(128))
    address = db.Column(db.String(128))

    events = db.relationship('Event', backref='client', lazy='dynamic',
                             query_class=ExtraOut, primaryjoin="and_("
                             "Client.zone_id==foreign(Event.zone_id), "
                             "Client.name==foreign(Event.client_name))")

    results = db.relationship('Result', backref='client', lazy='dynamic',
                              query_class=ExtraOut, primaryjoin="and_("
                              "Client.zone_id==foreign(Result.zone_id), "
                              "Client.name==foreign(Result.client_name))")

    silences = db.relationship('Silence', backref='client', lazy='dynamic',
                               query_class=ExtraOut, primaryjoin="and_("
                               "Client.zone_id == foreign("
                               "Silence.zone_id), "
                               "Client.name == foreign(Silence.client_name))")

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_id'], ['monitoring_zones.id'],
                                ondelete='CASCADE'),
        db.UniqueConstraint('zone_id', 'name', name='client_uc'),
    )

    def __init__(self, zone, extra):
        raise NotImplementedError

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
        return bool(self.silences.filter(Silence.check_name == '').first())

    @property
    def dict_out(self):
        return {
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
                              query_class=ExtraOut,
                              primaryjoin="and_("
                              "Check.zone_id==foreign(Result.zone_id), "
                              "Check.name==foreign(Result.check_name))")
    events = db.relationship('Event', backref='check', lazy='dynamic',
                             query_class=ExtraOut,
                             primaryjoin="and_("
                             "Check.zone_id==foreign(Event.zone_id), "
                             "Check.name==foreign(Event.check_name))")

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_id'], ['monitoring_zones.id'],
                                ondelete='CASCADE'),
        db.UniqueConstraint('zone_id', 'name', name='check_uc'),
    )

    def __init__(self, zone, extra):
        raise NotImplementedError

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('check', cls.name))

    @property
    def dict_out(self):
        return {
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

    class ResultQuery(ExtraOut):

        def all_dict_out(self):
            clients_silences = self.outerjoin(Silence, db.and_(
                Result.zone_name == Silence.zone_name,
                Result.client_name == Silence.client_name,
                Result.check_name == Silence.check_name)).add_entity(
                    Silence).all()
            events_json = []
            for event, silence in clients_silences:
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
        raise NotImplementedError

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('check', cls.check_name),
                ('client', cls.client_name))

    @property
    def dict_out(self):
        return {
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

    class EventQuery(ExtraOut):

        def all_dict_out(self):
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
                event_json = event.dict_out
                event_json['silenced'] = bool(silence)
                events_json.append(event_json)
            return events_json

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
                               query_class=ExtraOut,
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
        raise NotImplementedError

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('check', cls.check_name),
                ('client', cls.client_name))

    @property
    def dict_out(self):
        return {
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
        raise NotImplementedError

    @classmethod
    def get_filters_maps(cls):
        return (('zone', cls.zone_name), ('check', cls.check_name),
                ('client', cls.client_name))

    @property
    def dict_out(self):
        return {
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


class Zone(TimeStampMixin, BaseCache, db.Model):

    entity = 'zones'
    __tablename__ = 'monitoring_zones'

    models = [Check, Client, Event, Silence, Result]

    name = db.Column(db.String(64))
    _enabled = db.Column('enabled', db.Boolean(), default=0)
    status = db.Column(db.String(64))
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
                              query_class=ExtraOut)
    checks = db.relationship('Check', backref='zone', lazy='dynamic',
                             query_class=ExtraOut)
    events = db.relationship('Event', backref='zone', lazy='dynamic',
                             query_class=ExtraOut)
    results = db.relationship('Result', backref='zone', lazy='dynamic',
                              query_class=ExtraOut)
    silences = db.relationship('Silence', backref='zone', lazy='dynamic',
                               query_class=ExtraOut)

    __table_args__ = (
        db.UniqueConstraint('name'),
    )

    def __init__(self, name, enabled=0, host=None, path=None, protocol='http',
                 port=80, timeout=30, interval=30, username=None, password=None,
                 verify_ssl=True, **kwargs):
        self.name = name
        self.enabled = enabled
        if self.enabled:
            self.status = 'creating'
            self.status_message = 'The zone is being created'
        else:
            self.status = 'disabled'
            self.status_message = 'The zone is disabled'
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
    def get_filters_maps(cls):
        return (('zone', cls.name),)

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if int(value) == 0:
            self._enabled = 0
            self.status = 'disabled'
            self.status_message = 'The zone is disabled'
        if int(value) == 1:
            self._enabled = 1
            self.status = 'enabling'
            self.status_message = 'The zone is being enabled'

    enabled = synonym('_enabled', descriptor=enabled)

    @classmethod
    def create_zone(cls, name, backend, **kwargs):
        zone = driver.DriverManager(
            namespace='opsy.monitoring.backend',
            name=backend,
            invoke_on_load=True,
            invoke_args=(name,),
            invoke_kwds=(kwargs)).driver
        db.session.add(zone)
        db.session.commit()
        return zone

    @classmethod
    def get_zone_by_id(cls, zone_id):
        return cls.query.filter(cls.id == zone_id).first()

    @classmethod
    def get_zone_by_name(cls, name):
        return cls.query.filter(cls.name == name).first()

    @classmethod
    def get_zones(cls):
        return cls.query.all()

    @classmethod
    def delete_zone(cls, zone_id):
        cls.query.filter(cls.id == zone_id).delete()
        db.session.commit()

    @classmethod
    def update_zone(cls, zone_id, **kwargs):
        zone = cls.get_zone_by_id(zone_id)
        for k, v in kwargs.items():
            setattr(zone, k, v)
        db.session.commit()
        return zone

    def query_api(self, uri):
        raise NotImplementedError

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
        overall_health, pollers = self.pollers_health
        return {
            'name': self.name,
            'backend': self.backend,
            'status': self.status,
            'status_message': self.status_message,
            'last_poll_time': self.last_poll_time
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
                model.__tablename__, self.name, exc)
            app.logger.error(message)
            # init_objects.extend(model.update_last_poll(
            #     self.name, 'critical', message))
            return del_objects, init_objects
        del_objects = [model.query.filter(model.zone_id == self.id)]
        # init_objects.extend(model.update_last_poll(self.name, 'ok', 'Success'))
        for result in results:
            init_objects.append(model(self, result))
        app.logger.info('Updated %s cache for %s' % (
            model.__tablename__, self.name))
        return del_objects, init_objects
