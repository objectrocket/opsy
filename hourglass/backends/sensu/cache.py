from flask import json
from ..cache import *


# Laying out the framework for the api caching layer.
# class Node(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'nodes'


class SensuClient(Client):
    uri = 'clients'

    def __init__(self, datacenter, extra):
        self.datacenter = datacenter
        self.name = extra['name']
        extra['datacenter'] = datacenter
        self.extra = json.dumps(extra)


class SensuCheck(Check):
    uri = 'checks'

    def __init__(self, datacenter, extra):
        self.datacenter = datacenter
        self.name = extra['name']
        extra['datacenter'] = datacenter
        self.extra = json.dumps(extra)


class SensuResult(Result):
    uri = 'results'

    def __init__(self, datacenter, extra):
        self.datacenter = datacenter
        self.extra = extra
        self.client_name = extra['client']
        self.check_name = extra['check']['name']
        self.status = extra['check']['status']
        extra['datacenter'] = datacenter
        self.extra = json.dumps(extra)


# class SensuAggregate(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'aggregates'


class SensuEvent(Event):
    uri = 'events'

    def __init__(self, datacenter, extra):
        self.datacenter = datacenter
        self.client_name = extra['client']['name']
        self.check_name = extra['check']['name']
        self.check_occurrences = extra['check'].get('occurrences')
        self.event_occurrences = extra['occurrences']
        self.status = extra['check']['status']
        extra['datacenter'] = datacenter
        self.extra = json.dumps(extra)


class SensuStash(Stash):
    uri = 'stashes'

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
