import asyncio
from hourglass.backends.cache import *
from hourglass.backends import db


class Poller(object):

    def __init__(self, app, name, config):
        self.models = [Check, Client, Event, Stash, Result]
        self.app = app
        self.name = name
        self.host = config.get('host')
        self.port = config.get('port')
        self.timeout = int(config.get('timeout', 10))

    def query_api(self, uri):
        raise NotImplementedError

    @asyncio.coroutine
    def update_objects(self, model):
        self.app.logger.debug("Updating %s cache for %s" % (
            model.__tablename__, self.name))
        results = self.query_api(model.uri)
        if results is None:
            # bail out and don't touch the existing cache if something broke
            return []
        self.app.logger.debug('Purging cache %s for %s' % (
                              model.__tablename__, self.name))
        model.query.filter(model.datacenter == self.name).delete()
        init_objects = []
        for result in results:
            init_objects.append(model(self.name, result))
        self.app.logger.debug("Updated %s cache for %s" % (
            model.__tablename__, self.name))
        return init_objects

    @asyncio.coroutine
    def update_cache(self):
        self.app.logger.debug('Updating Cache for %s' % self.name)
        with self.app.app_context():
            tasks = []
            for model in self.models:
                tasks.append(asyncio.async(self.update_objects(model)))
            results = yield from asyncio.gather(*tasks)
            for result in results:
                db.session.bulk_save_objects(result)
            db.session.commit()
        self.app.logger.debug("Cache update complete")

    def __repr__(self):
        return '<Poller base/%s>' % self.name
