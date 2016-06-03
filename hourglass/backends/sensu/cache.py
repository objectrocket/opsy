import aiohttp
import asyncio
from flask import json
from ..cache import *


class SensuZone(Zone):

    def __init__(self, name, host, port, timeout):
        self.models = [SensuCheck, SensuClient, SensuEvent, SensuStash,
                       SensuResult]
        self.backend_type = 'sensu'
        self.name = name
        self.host = host
        self.port = port
        self.timeout = timeout

    @asyncio.coroutine
    def query_api(self, session, url):
        with aiohttp.Timeout(self.timeout):
            response = yield from session.get(url)
            return (yield from response.json())

    @asyncio.coroutine
    def update_objects(self, app, loop, model):
        init_objects = []
        try:
            with aiohttp.ClientSession(loop=loop) as session:
                url = "http://%s:%s/%s" % (self.host, self.port, model.uri)
                app.logger.debug('Making request to %s' % url)
                results = yield from self.query_api(session, url)
        except Exception as e:
            app.logger.error('Error updating %s cache for %s: %s' % (
                model.__tablename__, self.name, e))
            return init_objects
        model.query.filter(model.zone_name == self.name).delete()
        for result in results:
            init_objects.append(model(self.name, result))
        app.logger.info('Updated %s cache for %s' % (
            model.__tablename__, self.name))
        return init_objects


class SensuZoneMetadata(ZoneMetadata):

    def __init__(self, zone_name, key, value):
        self.zone_name = zone_name
        self.key = key
        self.value = value


class SensuClient(Client):
    uri = 'clients'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.name = extra['name']
        extra['zone_name'] = zone_name
        self.extra = json.dumps(extra)


class SensuCheck(Check):
    uri = 'checks'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.name = extra['name']
        extra['zone_name'] = zone_name
        self.extra = json.dumps(extra)


class SensuResult(Result):
    uri = 'results'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.extra = extra
        self.client_name = extra['client']
        self.check_name = extra['check']['name']
        self.status = extra['check']['status']
        extra['zone_name'] = zone_name
        self.extra = json.dumps(extra)


# class SensuAggregate(db.Model):
#     __bind_key__ = 'cache'
#     __tablename__ = 'aggregates'


class SensuEvent(Event):
    uri = 'events'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.client_name = extra['client']['name']
        self.check_name = extra['check']['name']
        self.check_occurrences = extra['check'].get('occurrences')
        self.event_occurrences = extra['occurrences']
        self.status = extra['check']['status']
        extra['zone_name'] = zone_name
        self.extra = json.dumps(extra)


class SensuStash(Stash):
    uri = 'stashes'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
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
        extra['zone_name'] = self.zone_name
        extra['check_name'] = self.check_name
        extra['client_name'] = self.client_name
        extra['flavor'] = self.flavor
        self.extra = json.dumps(extra)
