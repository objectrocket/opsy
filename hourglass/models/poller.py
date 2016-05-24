import asyncio
import aiohttp
from hourglass.models.backends.sensu.cache import Check, Client, Event, Stash, Result
from hourglass.models.backends import db


class Poller(object):
    def __init__(self, app):
        self.sensu_models = [Check, Client, Event, Stash, Result]
        self.app = app
        self.db = db
        self.sensus = self.app.config['sensu_nodes']
        self.interval = self.app.config['hourglass'].get('poll_interval', 10)
        self.loop = asyncio.get_event_loop()
        self.httpsession = aiohttp.ClientSession(loop=self.loop)

    @asyncio.coroutine
    def query_sensu(self, details, uri):
        timeout = int(details.get('timeout', 5))
        url = "http://%s:%s/%s" % (details['host'], details['port'], uri)
        out_dict = {}
        try:
            with aiohttp.Timeout(timeout):
                response = yield from self.httpsession.get(url)
                out_dict = yield from response.json()
                response.release()
        except:
            self.app.logger.debug("Reached timeout on request to %s" % url)
        return (out_dict)

    @asyncio.coroutine
    def update_sensu_object(self, name, details, model):
        self.app.logger.debug("Updating %s cache for %s" % (
            model.__tablename__, name))
        checks = yield from self.query_sensu(details, model.__tablename__)
        init_objects = []
        for check in checks:
            init_objects.append(model(name, check))
        self.app.logger.debug("Updated %s cache for %s" % (
            model.__tablename__, name))
        return init_objects

    def update_cache(self):
        self.app.logger.debug('Updating Cache')
        with self.app.app_context():
            tasks = []
            for name, details in self.sensus.items():
                for model in self.sensu_models:
                    self.app.logger.debug('Purging cache %s for %s' % (model.__tablename__, name))
                    model.query.filter(model.datacenter == name).delete()
                    tasks.append(asyncio.async(self.update_sensu_object(name, details, model)))
            self.loop.run_until_complete(asyncio.wait(tasks))
            for task in tasks:
                self.db.session.bulk_save_objects(task.result())
            self.db.session.commit()
        self.app.logger.debug("Cache update complete")
