import asyncio
import aiohttp
from hourglass.backends.cache import *


class Poller(object):

    def __init__(self, app, loop, name, config):
        self.models = [Check, Client, Event, Stash, Result]
        self.app = app
        self.loop = loop
        self.name = name
        self.host = config.get('host')
        self.port = config.get('port')
        self.timeout = int(config.get('timeout', 10))

    def query_api(self, uri):
        raise NotImplementedError

    @asyncio.coroutine
    def update_objects(self, model):
        init_objects = []
        try:
            with aiohttp.ClientSession(loop=self.loop) as session:
                results = yield from self.query_api(session, model.uri)
        except aiohttp.errors.ClientError as e:
            self.app.logger.error('Error updating %s cache for %s: %s' % (
                model.__tablename__, self.name, e))
            return init_objects
        model.query.filter(model.datacenter == self.name).delete()
        for result in results:
            init_objects.append(model(self.name, result))
        self.app.logger.debug('Updated %s cache for %s' % (
            model.__tablename__, self.name))
        return init_objects

    def get_update_tasks(self):
        tasks = []
        for model in self.models:
            tasks.append(asyncio.async(self.update_objects(model)))
        return tasks

    def __repr__(self):
        return '<Poller base/%s>' % self.name
