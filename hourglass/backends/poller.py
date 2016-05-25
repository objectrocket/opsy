import asyncio
from hourglass.backends.cache import *
from hourglass.backends import db


class Poller(object):

    def __init__(self, name, config):
        self.models = [Check, Client, Event, Stash, Result]
        self.name = name
        self.host = config.get('host')
        self.port = config.get('port')
        self.timeout = int(config.get('timeout', 10))

    def query_api(self, uri):
        raise NotImplementedError

    @asyncio.coroutine
    def update_objects(self, app, model):
        app.logger.debug('Updating %s cache for %s' % (
            model.__tablename__, self.name))
        results = self.query_api(app, model.uri)
        if results is None:
            # bail out and don't touch the existing cache if something broke
            return []
        app.logger.debug('Purging cache %s for %s' % (
            model.__tablename__, self.name))
        model.query.filter(model.datacenter == self.name).delete()
        init_objects = []
        for result in results:
            init_objects.append(model(self.name, result))
        app.logger.debug('Updated %s cache for %s' % (
            model.__tablename__, self.name))
        return init_objects

    @asyncio.coroutine
    def update_cache(self, app):
        app.logger.debug('Updating Cache for %s' % self.name)
        tasks = []
        for model in self.models:
            tasks.append(asyncio.async(self.update_objects(app, model)))
        results = yield from asyncio.gather(*tasks)
        for result in results:
            db.session.bulk_save_objects(result)
        db.session.commit()
        app.logger.debug('Cache update complete for %s' % self.name)

    def __repr__(self):
        return '<Poller base/%s>' % self.name
