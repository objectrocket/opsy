import requests
from time import time
# from . import db


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


# class Client(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'clients'


# class Check(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'checks'


# class Result(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'results'


# class Aggregate(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'aggregates'


# class Event(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'events'


# class Stash(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'stashes'
