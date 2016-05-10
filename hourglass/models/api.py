from datetime import datetime
from flask import json
from . import db, HourglassCacheMixin


# UCHIWA_URL = db.get_app().config.get('uchiwa_url')


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

    events = db.relationship('Event', backref='client', lazy='dynamic')

    def __init__(self, datacenter, name, extra, timestamp=None):
        self.datacenter = datacenter
        self.name = name
        extra['datacenter'] = datacenter
        # extra['href'] = '%s/#/client/%s/%s' % (UCHIWA_URL, self.datacenter,
        #                                        self.name)
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
        # extra['href'] = '%s/#/client/%s/%s?check=%s' % (
        #     UCHIWA_URL, self.datacenter, self.clientname, self.checkname)
        self.extra = json.dumps(extra)

    def __repr__(self):
        return '<Event %s/%s/%s>' % (self.datacenter, self.clientname,
                                     self.checkname)


# class Stash(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'stashes'
