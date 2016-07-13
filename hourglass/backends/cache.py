import asyncio
from hourglass.utils import get_filters_list
from . import db, ExtraOut, CacheBase


class Client(CacheBase, db.Model):

    class ClientQuery(ExtraOut):

        def all_dict_out(self):
            clients_silences = self.outerjoin(Silence, db.and_(
                Client.zone_name == Silence.zone_name,
                Client.name == Silence.client_name,
                Silence.check_name == '')).add_entity(Silence).all()
            clients_json = []
            for client, silence in clients_silences:
                client_json = client.dict_out
                if silence:
                    client_json['silenced'] = True
                else:
                    client_json['silenced'] = False
                clients_json.append(client_json)
            return clients_json

    query_class = ClientQuery
    __bind_key__ = 'cache'
    __tablename__ = 'clients'

    zone_name = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256), primary_key=True)

    events = db.relationship('Event', backref='client', lazy='dynamic',
                             query_class=ExtraOut, primaryjoin="and_("
                             "Client.zone_name==foreign(Event.zone_name), "
                             "Client.name==foreign(Event.client_name))")

    results = db.relationship('Result', backref='client', lazy='dynamic',
                              query_class=ExtraOut, primaryjoin="and_("
                              "Client.zone_name==foreign(Result.zone_name), "
                              "Client.name==foreign(Result.client_name))")

    silences = db.relationship('Silence', backref='client', lazy='dynamic',
                               query_class=ExtraOut, primaryjoin="and_("
                               "Client.zone_name == foreign("
                               "Silence.zone_name), "
                               "Client.name == foreign(Silence.client_name))")

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_name'], ['zones.name']),
    )

    def __init__(self, zone_name, extra):
        raise NotImplemented

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
        if self.silences.filter(Silence.check_name == '').first():
            return True
        else:
            return False

    @classmethod
    def get_dashboard_filters_list(cls, config, dashboard):
        if config['dashboards'].get(dashboard) is None:
            return ()
        zones = config['dashboards'][dashboard].get('zone')
        clients = config['dashboards'][dashboard].get('client')
        filters = ((zones, cls.zone_name),
                   (clients, cls.name))
        return get_filters_list(filters)

    @property
    def dict_out(self):
        return {
            'zone_name': self.zone_name,
            'backend': self.backend,
            'name': self.name
        }

    def __repr__(self):
        return '<%s %s/%s>' % (self.__class__.__name__, self.zone_name,
                               self.name)


class Check(CacheBase, db.Model):

    __bind_key__ = 'cache'
    __tablename__ = 'checks'

    zone_name = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256), primary_key=True)
    occurrences_threshold = db.Column(db.BigInteger)
    interval = db.Column(db.BigInteger)
    command = db.Column(db.Text)

    results = db.relationship('Result', backref='check', lazy='dynamic',
                              query_class=ExtraOut,
                              primaryjoin="and_("
                              "Check.zone_name==foreign(Result.zone_name), "
                              "Check.name==foreign(Result.check_name))")
    events = db.relationship('Event', backref='check', lazy='dynamic',
                             query_class=ExtraOut,
                             primaryjoin="and_("
                             "Check.zone_name==foreign(Event.zone_name), "
                             "Check.name==foreign(Event.check_name))")

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_name'], ['zones.name']),
    )

    def __init__(self, zone_name, extra):
        raise NotImplemented

    @classmethod
    def get_dashboard_filters_list(cls, config, dashboard):
        if config['dashboards'].get(dashboard) is None:
            return ()
        zones = config['dashboards'][dashboard].get('zone')
        checks = config['dashboards'][dashboard].get('check')
        filters = ((zones, cls.zone_name),
                   (checks, cls.name))
        return get_filters_list(filters)

    @property
    def dict_out(self):
        return {
            'zone_name': self.zone_name,
            'backend': self.backend,
            'name': self.name,
            'occurrences_threshold': self.occurrences_threshold,
            'interval': self.interval,
            'command': self.command
        }

    def __repr__(self):
        return '<%s %s/%s>' % (self.__class__.__name__, self.zone_name,
                               self.name)


class Result(CacheBase, db.Model):

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
                if silence:
                    event_json['silenced'] = True
                else:
                    event_json['silenced'] = False
                events_json.append(event_json)
            return events_json

    query_class = ResultQuery
    __bind_key__ = 'cache'
    __tablename__ = 'results'

    zone_name = db.Column(db.String(64), primary_key=True)
    client_name = db.Column(db.String(256), primary_key=True)
    check_name = db.Column(db.String(256), primary_key=True)
    occurrences_threshold = db.Column(db.BigInteger)
    status = db.Column(db.String(256))
    interval = db.Column(db.BigInteger)
    command = db.Column(db.Text)
    output = db.Column(db.Text)

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_name'], ['zones.name']),
        db.CheckConstraint(status.in_(
            ['ok', 'warning', 'critical', 'unknown']))
    )

    def __init__(self, zone_name, extra):
        raise NotImplemented

    @classmethod
    def get_dashboard_filters_list(cls, config, dashboard):
        if config['dashboards'].get(dashboard) is None:
            return ()
        zones = config['dashboards'][dashboard].get('zone')
        checks = config['dashboards'][dashboard].get('check')
        clients = config['dashboards'][dashboard].get('client')
        statuses = config['dashboards'][dashboard].get('status')
        filters = ((zones, cls.zone_name),
                   (checks, cls.check_name),
                   (clients, cls.client_name),
                   (statuses, cls.status))
        return get_filters_list(filters)

    @property
    def dict_out(self):
        return {
            'zone_name': self.zone_name,
            'backend': self.backend,
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


class Event(CacheBase, db.Model):

    class EventQuery(ExtraOut):

        def all_dict_out(self):
            clients_silences = self.outerjoin(Silence, db.and_(
                Event.zone_name == Silence.zone_name,
                Event.client_name == Silence.client_name,
                Event.check_name.in_(
                    [Silence.check_name, '']))).add_entity(Silence).all()
            events_json = []
            for event, silence in clients_silences:
                event_json = event.dict_out
                if silence:
                    event_json['silenced'] = True
                else:
                    event_json['silenced'] = False
                events_json.append(event_json)
            return events_json

    query_class = EventQuery
    __bind_key__ = 'cache'
    __tablename__ = 'events'

    zone_name = db.Column(db.String(64), primary_key=True)
    client_name = db.Column(db.String(256), primary_key=True)
    check_name = db.Column(db.String(256), primary_key=True)
    occurrences_threshold = db.Column(db.BigInteger)
    occurrences = db.Column(db.BigInteger)
    status = db.Column(db.String(256))
    command = db.Column(db.Text)
    interval = db.Column(db.BigInteger)
    output = db.Column(db.Text)

    silences = db.relationship('Silence', backref='events', lazy='dynamic',
                               query_class=ExtraOut,
                               primaryjoin="and_("
                               "Event.zone_name==foreign(Silence.zone_name),"
                               "Event.client_name==foreign("
                               "Silence.client_name), "
                               "Event.check_name==foreign("
                               "Silence.check_name))")

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_name'], ['zones.name']),
        db.CheckConstraint(status.in_(
            ['ok', 'warning', 'critical', 'unknown']))
    )

    def __init__(self, zone_name, extra):
        raise NotImplemented

    @classmethod
    def get_dashboard_filters_list(cls, config, dashboard):
        if config['dashboards'].get(dashboard) is None:
            return ()
        zones = config['dashboards'][dashboard].get('zone')
        checks = config['dashboards'][dashboard].get('check')
        clients = config['dashboards'][dashboard].get('client')
        statuses = config['dashboards'][dashboard].get('status')
        filters = ((zones, cls.zone_name),
                   (checks, cls.check_name),
                   (clients, cls.client_name),
                   (statuses, cls.status))
        return get_filters_list(filters)

    @property
    def dict_out(self):
        return {
            'backend': self.backend,
            'zone_name': self.zone_name,
            'client_name': self.client_name,
            'check_name': self.check_name,
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


class Silence(CacheBase, db.Model):

    __bind_key__ = 'cache'
    __tablename__ = 'silences'

    zone_name = db.Column(db.String(64), primary_key=True)
    client_name = db.Column(db.String(256), primary_key=True)
    check_name = db.Column(db.String(256), nullable=True, primary_key=True,
                           default="")
    created_at = db.Column(db.DateTime)
    expire_at = db.Column(db.DateTime)
    comment = db.Column(db.Text)

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_name'], ['zones.name']),
    )

    def __init__(self, zone_name, extra):
        raise NotImplemented

    @property
    def dict_out(self):
        return {
            'zone_name': self.zone_name,
            'backend': self.backend,
            'client_name': self.client_name,
            'check_name': self.check_name,
            'created_at': self.created_at,
            'expire_at': self.expire_at,
            'comment': self.comment
        }

    def __repr__(self):
        return '<%s %s/%s/%s>' % (self.__class__.__name__, self.zone_name,
                                  self.client_name, self.check_name)


class Zone(CacheBase, db.Model):

    __bind_key__ = 'cache'
    __tablename__ = 'zones'

    models = [Check, Client, Event, Silence, Result]

    name = db.Column(db.String(64), primary_key=True)
    host = db.Column(db.String(64))
    path = db.Column(db.String(64))
    protocol = db.Column(db.String(64))
    port = db.Column(db.Integer())
    timeout = db.Column(db.Integer())
    username = db.Column(db.String(64))
    password = db.Column(db.String(64))

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

    def __init__(self, name, host=None, path=None, protocol=None, port=None,
                 timeout=None, username=None, password=None):
        self.name = name
        self.host = host
        self.path = path
        self.protocol = protocol
        self.port = port
        self.timeout = timeout
        self.username = username
        self.password = password

    def query_api(self, uri):
        raise NotImplementedError

    @asyncio.coroutine
    def update_objects(self, model):
        raise NotImplementedError

    def get_update_tasks(self, app, loop):
        tasks = []
        for model in self.models:
            tasks.append(asyncio.async(self.update_objects(app, loop, model)))
        return tasks

    @classmethod
    def get_dashboard_filters_list(cls, config, dashboard):
        if config['dashboards'].get(dashboard) is None:
            return ()
        zones = config['dashboards'][dashboard].get('zone')
        filters = ((zones, cls.name),)
        return get_filters_list(filters)

    @property
    def pollers_health(self):
        pollers = []
        overall_health = []
        for model in self.models:
            updated_at, status = model.last_poll_status(self.name)
            pollers.append({'name': model.__tablename__,
                            'updated_at': updated_at.isoformat(),
                            'status': status})
            overall_health.append(True) if status == 'ok' else \
                overall_health.append(False)
        if all(overall_health):
            overall_health = 'ok'
        elif any(overall_health):
            overall_health = 'warning'
        else:
            overall_health = 'critical'
        return overall_health, pollers

    @property
    def dict_out(self):
        overall_health, pollers = self.pollers_health
        return {
            'name': self.name,
            'backend': self.backend,
            'status': overall_health,
            'pollers': pollers
        }

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)
