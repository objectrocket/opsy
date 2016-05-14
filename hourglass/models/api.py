from datetime import datetime
from flask import json
from . import db, ExtraOut, HourglassCacheMixin


# Laying out the framework for the api caching layer.
# class Node(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'nodes'


class Client(HourglassCacheMixin, db.Model):
    __bind_key__ = 'cache'
    __tablename__ = 'clients'
    datacenter = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256), primary_key=True)
    timestamp = db.Column(db.DateTime)
    extra = db.Column(db.Text)

    events = db.relationship('Event', backref='client', lazy='dynamic',
                             query_class=ExtraOut)

    def __init__(self, datacenter, name, extra, timestamp=None):
        self.datacenter = datacenter
        self.name = name
        extra['datacenter'] = datacenter
        self.extra = json.dumps(extra)
        try:
            self.timestamp = datetime.fromtimestamp(timestamp)
        except TypeError:
            self.timestamp = None

    def __repr__(self):
        return '<Client %s/%s>' % (self.datacenter, self.name)


class Check(HourglassCacheMixin, db.Model):
    __bind_key__ = 'cache'
    __tablename__ = 'checks'
    datacenter = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256), primary_key=True)
    extra = db.Column(db.Text)

    def __init__(self, datacenter, name, extra):
        self.datacenter = datacenter
        self.name = name
        extra['datacenter'] = datacenter
        self.extra = json.dumps(extra)

    def __repr__(self):
        return '<Check %s/%s>' % (self.datacenter, self.name)


# class Result(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'results'


# class Aggregate(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'aggregates'


class Event(HourglassCacheMixin, db.Model):
    __bind_key__ = 'cache'
    __tablename__ = 'events'
    datacenter = db.Column(db.String(64), primary_key=True)
    clientname = db.Column(db.String(256), primary_key=True)
    checkname = db.Column(db.String(256), primary_key=True)
    checkoutput = db.Column(db.Text)
    checkoccurrences = db.Column(db.BigInteger)
    eventoccurrences = db.Column(db.BigInteger)
    status = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    extra = db.Column(db.Text)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['datacenter', 'clientname'],
            ['clients.datacenter', 'clients.name']
        ),
        db.ForeignKeyConstraint(
            ['datacenter', 'clientname', 'checkname'],
            ['stashes.datacenter', 'stashes.clientname', 'stashes.checkname']
        )
    )

    def __init__(self, datacenter, clientname, occurrences, status, timestamp,
                 extra):
        self.datacenter = datacenter
        self.clientname = clientname
        self.checkname = extra['check']['name']
        self.checkoutput = extra['check']['output']
        self.checkoccurrences = extra['check'].get('occurrences')
        self.eventoccurrences = occurrences
        self.status = status
        self.timestamp = datetime.fromtimestamp(timestamp)
        extra['datacenter'] = datacenter
        self.extra = json.dumps(extra)

    def __repr__(self):
        return '<Event %s/%s/%s>' % (self.datacenter, self.clientname,
                                     self.checkname)


class Stash(HourglassCacheMixin, db.Model):
    __bind_key__ = 'cache'
    __tablename__ = 'stashes'
    datacenter = db.Column(db.String(64), primary_key=True)
    path = db.Column(db.String(256), primary_key=True)
    clientname = db.Column(db.String(256), primary_key=True)
    checkname = db.Column(db.String(256), nullable=True, primary_key=True)
    source = db.Column(db.String(64))
    flavor = db.Column(db.String(64))
    created_at = db.Column(db.DateTime)
    expire_at = db.Column(db.DateTime)
    extra = db.Column(db.Text)

    events = db.relationship('Event', backref='stash', lazy='dynamic',
                             query_class=ExtraOut, viewonly=True)

    def __init__(self, datacenter, path, extra):
        self.datacenter = datacenter
        self.path = path
        extra['datacenter'] = datacenter
        self.extra = json.dumps(extra)
        if extra.get('expire') == -1:
            self.expire_at = None
        else:
            self.expire_at = datetime.fromtimestamp(
                int(datetime.utcnow().strftime("%s")) + extra['expire'])
        try:
            path_list = path.split('/')
            self.flavor = path_list[0]
            self.clientname = path_list[1]
            try:
                self.checkname = path_list[2]
            except IndexError:
                self.checkname = None
            self.source = extra['content']['source']
            self.created_at = datetime.fromtimestamp(
                extra['content']['timestamp'])
        except:
            self.flavor = None
            self.clientname = None
            self.checkname = None
            self.source = None
            self.created_at = None
            self.expire_at = None

    def __repr__(self):
        return '<Stash %s/%s>' % (self.datacenter, self.path)
