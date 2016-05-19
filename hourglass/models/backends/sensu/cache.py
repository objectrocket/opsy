from flask import json
from .. import db, ExtraOut, HourglassCacheMixin


# Laying out the framework for the api caching layer.
# class Node(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'nodes'


class Client(HourglassCacheMixin, db.Model):
    __bind_key__ = 'cache'
    __tablename__ = 'clients'
    datacenter = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256), primary_key=True)
    extra = db.Column(db.Text)

    events = db.relationship('Event', backref='client', lazy='dynamic',
                             query_class=ExtraOut)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['datacenter', 'name'],
            ['stashes.datacenter', 'stashes.client_name']
        ),
    )

    def __init__(self, datacenter, extra):
        self.datacenter = datacenter
        self.name = extra['name']
        extra['datacenter'] = datacenter
        self.extra = json.dumps(extra)

    def __repr__(self):
        return '<Client %s/%s>' % (self.datacenter, self.name)


class Check(HourglassCacheMixin, db.Model):
    __bind_key__ = 'cache'
    __tablename__ = 'checks'
    datacenter = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256), primary_key=True)
    extra = db.Column(db.Text)

    def __init__(self, datacenter, extra):
        self.datacenter = datacenter
        self.name = extra['name']
        extra['datacenter'] = datacenter
        self.extra = json.dumps(extra)

    def __repr__(self):
        return '<Check %s/%s>' % (self.datacenter, self.name)


class Result(HourglassCacheMixin, db.Model):
    __bind_key__ = 'cache'
    __tablename__ = 'results'
    datacenter = db.Column(db.String(64), primary_key=True)
    client_name = db.Column(db.String(256), primary_key=True)
    check_name = db.Column(db.String(256), primary_key=True)
    status = db.Column(db.Integer)
    extra = db.Column(db.Text)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['datacenter', 'client_name'],
            ['clients.datacenter', 'clients.name']
        ),
        db.ForeignKeyConstraint(
            ['datacenter', 'client_name', 'check_name'],
            ['stashes.datacenter', 'stashes.client_name', 'stashes.check_name']
        )
    )

    def __init__(self, datacenter, extra):
        self.datacenter = datacenter
        self.extra = extra
        self.client_name = extra['client']
        self.check_name = extra['check']['name']
        self.status = extra['check']['status']
        extra['datacenter'] = datacenter
        self.extra = json.dumps(extra)

    def __repr__(self):
        return '<Result %s/%s/%s>' % (self.datacenter, self.client_name,
                                      self.check_name)


# class Aggregate(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'aggregates'


class Event(HourglassCacheMixin, db.Model):
    __bind_key__ = 'cache'
    __tablename__ = 'events'
    datacenter = db.Column(db.String(64), primary_key=True)
    client_name = db.Column(db.String(256), primary_key=True)
    check_name = db.Column(db.String(256), primary_key=True)
    check_occurrences = db.Column(db.BigInteger)
    event_occurrences = db.Column(db.BigInteger)
    status = db.Column(db.Integer)
    extra = db.Column(db.Text)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['datacenter', 'client_name'],
            ['clients.datacenter', 'clients.name']
        ),
        db.ForeignKeyConstraint(
            ['datacenter', 'client_name', 'check_name'],
            ['stashes.datacenter', 'stashes.client_name', 'stashes.check_name']
        )
    )

    def __init__(self, datacenter, extra):
        self.datacenter = datacenter
        self.client_name = extra['client']['name']
        self.check_name = extra['check']['name']
        self.check_occurrences = extra['check'].get('occurrences')
        self.event_occurrences = extra['occurrences']
        self.status = extra['check']['status']
        extra['datacenter'] = datacenter
        self.extra = json.dumps(extra)

    def __repr__(self):
        return '<Event %s/%s/%s>' % (self.datacenter, self.client_name,
                                     self.check_name)


class Stash(HourglassCacheMixin, db.Model):
    __bind_key__ = 'cache'
    __tablename__ = 'stashes'
    datacenter = db.Column(db.String(64), primary_key=True)
    path = db.Column(db.String(256), primary_key=True)
    client_name = db.Column(db.String(256), primary_key=True)
    check_name = db.Column(db.String(256), nullable=True, primary_key=True)
    flavor = db.Column(db.String(64))
    extra = db.Column(db.Text)

    events = db.relationship('Event', backref='stash', lazy='dynamic',
                             query_class=ExtraOut, viewonly=True)
    client = db.relationship('Client', backref='stash', lazy='dynamic',
                             query_class=ExtraOut, viewonly=True)

    def __init__(self, datacenter, extra):
        self.datacenter = datacenter
        self.path = extra['path']
        try:
            path_list = self.path.split('/')
            self.flavor = path_list[0]
            self.client_name = path_list[1]
            try:
                self.check_name = path_list[2]
            except IndexError:
                self.check_name = None
            self.source = extra['content']['source']
        except:
            self.flavor = None
            self.client_name = None
            self.check_name = None
            self.source = None
            self.created_at = None
            self.expire_at = None
        extra['datacenter'] = self.datacenter
        extra['check_name'] = self.check_name
        extra['client_name'] = self.client_name
        extra['flavor'] = self.flavor
        self.extra = json.dumps(extra)

    def __repr__(self):
        return '<Stash %s/%s>' % (self.datacenter, self.path)
