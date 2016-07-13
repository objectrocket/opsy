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
        self.extra = json.dumps(extra)


class SensuCheck(SensuBase, Check):
    uri = 'checks'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.name = extra['name']
        self.occurrences_threshold = extra.get('occurrences')
        self.interval = extra.get('interval')
        self.command = extra.get('command')
        self.extra = json.dumps(extra)


class SensuResult(SensuBase, Result):
    uri = 'results'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.client_name = extra['client']
        self.check_name = extra['check']['name']
        status_map = ['ok', 'warning', 'critical']
        try:
            self.status = status_map[extra['check'].get('status')]
        except IndexError:
            self.status = 'unknown'
        self.occurrences_threshold = extra['check'].get('occurrences')
        self.command = extra['check'].get('command')
        self.output = extra['check'].get('output')
        self.interval = extra['check'].get('interval')
        self.extra = json.dumps(extra)


class SensuEvent(SensuBase, Event):
    uri = 'events'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.client_name = extra['client'].get('name')
        self.check_name = extra['check'].get('name')
        self.occurrences_threshold = extra['check'].get('occurrences')
        self.occurrences = extra['occurrences']
        status_map = ['ok', 'warning', 'critical']
        try:
            self.status = status_map[extra['check'].get('status')]
        except IndexError:
            self.status = 'unknown'
        self.command = extra['check'].get('command')
        self.output = extra['check'].get('output')
        self.interval = extra['check'].get('interval')
        self.extra = json.dumps(extra)


class SensuSilence(SensuBase, Silence):
    uri = 'stashes'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        path_list = extra['path'].split('/')
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

    @classmethod
    def filter_api_response(cls, response):
        return [x for x in response if x['path'].startswith('silence/')]


class SensuZone(SensuBase, Zone):

    models = [SensuCheck, SensuClient, SensuEvent, SensuSilence, SensuResult]

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
            try:
                results = model.filter_api_response(results)
            except NotImplementedError:
                pass
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
