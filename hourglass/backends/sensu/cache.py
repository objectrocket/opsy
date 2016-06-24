import aiohttp
import asyncio
from flask import json
from ..cache import *
from . import SensuBase
from datetime import datetime
from time import time


class SensuClient(SensuBase, Client):
    uri = 'clients'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.name = extra['name']
        extra['zone_name'] = zone_name
        self.extra = json.dumps(extra)


class SensuCheck(SensuBase, Check):
    uri = 'checks'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.name = extra['name']
        extra['zone_name'] = zone_name
        self.extra = json.dumps(extra)


class SensuResult(SensuBase, Result):
    uri = 'results'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.extra = extra
        self.client_name = extra['client']
        self.check_name = extra['check']['name']
        self.status = extra['check']['status']
        extra['zone_name'] = zone_name
        self.extra = json.dumps(extra)


class SensuEvent(SensuBase, Event):
    uri = 'events'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.client_name = extra['client'].get('name')
        self.check_name = extra['check'].get('name')
        self.occurrences_threshold = extra['check'].get('occurrences')
        self.occurrences = extra['occurrences']
        self.status = extra['check'].get('status')
        self.command = extra['check'].get('command')
        self.output = extra['check'].get('output')
        self.extra = json.dumps(extra)


class SensuStash(SensuBase, Stash):
    uri = 'stashes'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        path_list = extra['path'].split('/')
        self.flavor = path_list[0]
        self.client_name = path_list[1]
        try:
            self.check_name = path_list[2]
        except IndexError:
            self.check_name = None
        self.comment = json.dumps(extra['content'])
        if extra['content'].get('timestamp'):
            self.created_at = datetime.fromtimestamp(
                int(extra['content']['timestamp']))
        if extra['expire'] == -1:
            self.expire_at = None
        else:
            self.expire_at = datetime.fromtimestamp(
                int(time() + int(extra['expire'])))
        self.extra = json.dumps(extra)


class SensuZone(SensuBase, Zone):

    models = [SensuCheck, SensuClient, SensuEvent, SensuStash, SensuResult]

    def __init__(self, name, host, port, timeout):
        self.name = name
        self.host = host
        self.port = port
        self.timeout = timeout

    @asyncio.coroutine
    def get(self, session, url):
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
                results = yield from self.get(session, url)
        except aiohttp.errors.ClientError as e:
            app.logger.error('Error updating %s cache for %s: %s' % (
                model.__tablename__, self.name, e))
            init_objects.append(model.update_last_poll_status(
                self.name, 'critical'))
            return init_objects
        model.query.filter(model.zone_name == self.name).delete()
        init_objects.append(model.update_last_poll_status(
            self.name, 'ok'))
        for result in results:
            init_objects.append(model(self.name, result))
        app.logger.info('Updated %s cache for %s' % (
            model.__tablename__, self.name))
        return init_objects
