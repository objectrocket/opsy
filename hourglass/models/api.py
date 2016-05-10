from datetime import datetime
from time import time
import requests
from . import db, TimeStampMixin


def get_events(config, datacenter=None):
    # Temp functions for front-end testing until we get the caching and poller
    # running
    sensu_nodes = config.get('sensu_nodes')
    hourglass_config = config.get('hourglass')
    events = []
    if datacenter:
        hosts = {datacenter: sensu_nodes.get(datacenter)}
    else:
        hosts = sensu_nodes
    for name, details in hosts.iteritems():
        url = 'http://%s:%s/events' % (details['host'], details['port'])
        localevents = requests.get(url).json()
        for event in localevents:
            age = int(time() - event['timestamp'])
            event.update({'datacenter': name})
        events += localevents
    for event in events:
        uchiwa_url = '%s/#/client/%s/%s?check=%s' % (
            hourglass_config['uchiwa_url'], event['datacenter'],
            event['client']['name'], event['check']['name'])
        event.update({
            'lastcheck': age,
            'href': uchiwa_url})
    return events


def get_checks(config, datacenter=None):
    # Temp functions for front-end testing until we get the caching and poller
    # running
    sensu_nodes = config.get('sensu_nodes')
    checks = []
    if datacenter:
        hosts = {datacenter: sensu_nodes.get(datacenter)}
    else:
        hosts = sensu_nodes
    for name, details in hosts.iteritems():
        url = 'http://%s:%s/checks' % (details['host'], details['port'])
        localchecks = requests.get(url).json()
        for check in localchecks:
            check.update({'datacenter': name})
        checks += localchecks
    return checks


# Laying out the framework for the api caching layer.
# class Node(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'nodes'


class Client(TimeStampMixin, db.Model):
    __bind_key__ = 'cache'
    __tablename__ = 'clients'
    datacenter = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256), primary_key=True)
    timestamp = db.Column(db.DateTime)
    extra = db.Column(db.PickleType)

    def __init__(self, datacenter, name, timestamp, extra):
        self.datacenter = datacenter
        self.name = name
        self.extra = extra
        self.timestamp = datetime.fromtimestamp(timestamp)

    def __repr__(self):
        return '<Client %r/%r>' % (self.datacenter, self.name)


class Check(TimeStampMixin, db.Model):
    __bind_key__ = 'cache'
    __tablename__ = 'checks'
    datacenter = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256), primary_key=True)
    extra = db.Column(db.PickleType)

    def __init__(self, datacenter, name, extra):
        self.datacenter = datacenter
        self.name = name
        self.extra = extra

    def __repr__(self):
        return '<Check %r/%r>' % (self.datacenter, self.name)


# class Result(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'results'


# class Aggregate(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'aggregates'


class Event(TimeStampMixin, db.Model):
    __bind_key__ = 'cache'
    __tablename__ = 'events'
    datacenter = db.Column(db.String(64), primary_key=True)
    clientname = db.Column(db.String(256), primary_key=True)
    checkname = db.Column(db.String(256), primary_key=True)
    occurrences = db.Column(db.BigInteger)
    status = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    extra = db.Column(db.PickleType)

    def __init__(self, datacenter, clientname, checkname, occurrences, status, timestamp, extra):
        self.datacenter = datacenter
        self.clientname = clientname
        self.checkname = checkname
        self.occurrences = occurrences
        self.status = status
        self.timestamp = datetime.fromtimestamp(timestamp)
        self.extra = extra

    def __repr__(self):
        return '<Event %r/%r/%r>' % (self.datacenter, self.clientname, self.checkname)


# class Stash(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'stashes'
