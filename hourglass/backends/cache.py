import asyncio
from hourglass.utils import get_filters_list
from . import db, ExtraOut, CacheBase


class Client(CacheBase, db.Model):

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

    silences = db.relationship('Stash', backref='client', lazy='dynamic',
                               query_class=ExtraOut, primaryjoin="and_("
                               "Client.zone_name == foreign(Stash.zone_name), "
                               "Client.name == foreign(Stash.client_name), "
                               "foreign(Stash.flavor) == 'silence')")

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
        if self.silences.filter(Stash.check_name == '').first():
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
            'name': self.name,
            'status': self.status,
            'silenced': self.silenced,
        }
    # JOWETT LOOK AT THIS ^

    def __repr__(self):
        return '<%s %s/%s>' % (self.__class__.__name__, self.zone_name,
                               self.name)


class Check(CacheBase, db.Model):

    __bind_key__ = 'cache'
    __tablename__ = 'checks'

    zone_name = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256), primary_key=True)

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

    def __repr__(self):
        return '<%s %s/%s>' % (self.__class__.__name__, self.zone_name,
                               self.name)


class Result(CacheBase, db.Model):

    __bind_key__ = 'cache'
    __tablename__ = 'results'

    zone_name = db.Column(db.String(64), primary_key=True)
    client_name = db.Column(db.String(256), primary_key=True)
    check_name = db.Column(db.String(256), primary_key=True)
    status = db.Column(db.String(256))

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

    def __repr__(self):
        return '<%s %s/%s/%s>' % (self.__class__.__name__, self.zone_name,
                                  self.client_name, self.check_name)


class Event(CacheBase, db.Model):

    __bind_key__ = 'cache'
    __tablename__ = 'events'

    zone_name = db.Column(db.String(64), primary_key=True)
    client_name = db.Column(db.String(256), primary_key=True)
    check_name = db.Column(db.String(256), primary_key=True)
    occurrences_threshold = db.Column(db.BigInteger)
    occurrences = db.Column(db.BigInteger)
    status = db.Column(db.String(256))
    command = db.Column(db.Text)
    output = db.Column(db.Text)

    stash = db.relationship('Stash', backref='events', lazy='dynamic',
                            query_class=ExtraOut,
                            primaryjoin="and_("
                            "Event.zone_name==foreign(Stash.zone_name),"
                            "Event.client_name==foreign(Stash.client_name), "
                            "Event.check_name==foreign(Stash.check_name))")

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
            'command': self.command,
            'output': self.output,
        }

    def __repr__(self):
        return '<%s %s/%s/%s>' % (self.__class__.__name__, self.zone_name,
                                  self.client_name, self.check_name)


class Stash(CacheBase, db.Model):

    __bind_key__ = 'cache'
    __tablename__ = 'stashes'

    zone_name = db.Column(db.String(64), primary_key=True)
    client_name = db.Column(db.String(256), primary_key=True)
    check_name = db.Column(db.String(256), nullable=True, primary_key=True,
                           default="")
    created_at = db.Column(db.DateTime)
    expire_at = db.Column(db.DateTime)
    comment = db.Column(db.Text)
    flavor = db.Column(db.String(64))

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
            'comment': self.comment,
            'flavor': self.flavor,
        }

    def __repr__(self):
        return '<%s %s/%s/%s/%s>' % (self.__class__.__name__, self.zone_name,
                                     self.flavor, self.client_name,
                                     self.check_name)


class Zone(CacheBase, db.Model):

    __bind_key__ = 'cache'
    __tablename__ = 'zones'

    models = [Check, Client, Event, Stash, Result]

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
    stashes = db.relationship('Stash', backref='zone', lazy='dynamic',
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
