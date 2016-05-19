import asyncio
import aiohttp
from hourglass.models.backends.sensu.cache import Check, Client, Event, Stash
from hourglass.models.backends import db


class Poller(object):
    def __init__(self, app):
        self.app = app
        self.db = db
        self.httpsession = aiohttp.ClientSession()
        self.sensus = self.app.config['sensu_nodes']
        self.interval = self.app.config['hourglass'].get('poll_interval', 10)
        self.loop = asyncio.get_event_loop()

    @asyncio.coroutine
    def query_sensu(self, sensu, uri):
        url = "http://%s:%s/%s" % (sensu['host'], sensu['port'], uri)
        with aiohttp.Timeout(sensu['timeout']):
            response = yield from self.httpsession.get(url)
        return (yield from response.json())

    @asyncio.coroutine
    def update_sensu_checks(self, sensu):
        self.app.logger.debug("updating checks " + sensu['name'])
        checks = yield from self.query_sensu(sensu, 'checks')
        checkobjects = []
        for check in checks:
            checkobjects.append(Check(sensu['name'], check))
        self.app.logger.debug("updated checks " + sensu['name'])
        return checkobjects

    @asyncio.coroutine
    def update_sensu_clients(self, sensu):
        self.app.logger.debug("updating clients " + sensu['name'])
        clients = yield from self.query_sensu(sensu, 'clients')
        clientobjects = []
        for client in clients:
            clientobjects.append(Client(sensu['name'], client))
        self.app.logger.debug("updated clients " + sensu['name'])
        return clientobjects

    @asyncio.coroutine
    def update_sensu_events(self, sensu):
        self.app.logger.debug("updating events " + sensu['name'])
        events = yield from self.query_sensu(sensu, 'events')
        eventobjects = []
        for event in events:
            eventobjects.append(Event(sensu['name'], event))
        self.app.logger.debug("updated events " + sensu['name'])
        return eventobjects

    @asyncio.coroutine
    def update_sensu_stashes(self, sensu):
        self.app.logger.debug("updating stashes " + sensu['name'])
        stashes = yield from self.query_sensu(sensu, 'stashes')
        stashobjects = []
        for stash in stashes:
            stashobjects.append(Stash(sensu['name'], stash))
        self.app.logger.debug("updated stashes " + sensu['name'])
        return stashobjects

    def main(self):
        self.app.logger.debug('Updating Cache')
        tasks = []
        for sensu in self.sensus:
            tasks.append(asyncio.ensure_future(self.update_sensu_checks(self.sensus[sensu])))
            tasks.append(asyncio.ensure_future(self.update_sensu_clients(self.sensus[sensu])))
            tasks.append(asyncio.ensure_future(self.update_sensu_events(self.sensus[sensu])))
            tasks.append(asyncio.ensure_future(self.update_sensu_stashes(self.sensus[sensu])))
        with self.app.app_context():
            self.loop.run_until_complete(asyncio.wait(tasks))
            for sensu in self.sensus:
                Check.query.filter(Check.datacenter==sensu).delete()
                Client.query.filter(Client.datacenter==sensu).delete()
                Event.query.filter(Event.datacenter==sensu).delete()
                Stash.query.filter(Stash.datacenter==sensu).delete()
            for task in tasks:
                self.db.session.bulk_save_objects(task.result())
            self.db.session.commit()
        self.app.logger.debug("Cache update complete")
