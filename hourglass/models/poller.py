import asyncio
import aiohttp
from hourglass.models.backends.sensu.cache import Check, Client, Event, Stash
from hourglass.models.backends import db


class Poller(object):
    def __init__(self, app):
        self.app = app
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            db.session.commit()
        self.sensus = self.app.config['sensu_nodes']
        self.interval = self.app.config['hourglass'].get('poll_interval', 10)
        self.loop = asyncio.get_event_loop()

    @asyncio.coroutine
    def query_sensu(self, sensu, uri):
        url = "http://%s:%s/%s" % (sensu['host'], sensu['port'], uri)
        response = yield from aiohttp.get(url)
        return (yield from response.json())

    @asyncio.coroutine
    def update_sensu_checks(self, sensu):
        print("updating checks " + sensu['name'])
        checks = yield from self.query_sensu(sensu, 'checks')
        with self.app.app_context():
            Check.query.filter(Check.datacenter==sensu['name']).delete()
            for check in checks:
                db.session.add(Check(sensu['name'], check['name'], check))
            db.session.commit()
        print("updated checks " + sensu['name'])

    @asyncio.coroutine
    def update_sensu_clients(self, sensu):
        print("updating clients " + sensu['name'])
        clients = yield from self.query_sensu(sensu, 'clients')
        with self.app.app_context():
            Client.query.filter(Client.datacenter==sensu['name']).delete()
            for client in clients:
                try:
                    db.session.add(Client(sensu['name'], client['name'], client, client['timestamp']))
                except KeyError:
                    db.session.add(Client(sensu['name'], client['name'], client))
            db.session.commit()
        print("updated clients " + sensu['name'])

    @asyncio.coroutine
    def update_sensu_events(self, sensu):
        print("updating events " + sensu['name'])
        events = yield from self.query_sensu(sensu, 'events')
        with self.app.app_context():
            Event.query.filter(Event.datacenter==sensu['name']).delete()
            for event in events:
                db.session.add(Event(sensu['name'],
                                     event['client']['name'],
                                     event['occurrences'],
                                     event['check']['status'],
                                     event['timestamp'],
                                     event))
            db.session.commit()
        print("updated events " + sensu['name'])

    @asyncio.coroutine
    def update_sensu_stashes(self, sensu):
        print("updating stashes " + sensu['name'])
        stashes = yield from self.query_sensu(sensu, 'stashes')
        with self.app.app_context():
            Stash.query.filter(Stash.datacenter==sensu['name']).delete()
            for stash in stashes:
                db.session.add(Stash(sensu['name'], stash['path'], stash))
        #db.session.commit()
        print("updated stashes " + sensu['name'])

    def main(self):
        print('Updating Cache')
        tasks = []
        for sensu in self.sensus:
            tasks.append(self.update_sensu_checks(self.sensus[sensu]))
            tasks.append(self.update_sensu_clients(self.sensus[sensu]))
            tasks.append(self.update_sensu_events(self.sensus[sensu]))
            tasks.append(self.update_sensu_stashes(self.sensus[sensu]))
        self.loop.run_until_complete(asyncio.wait(tasks))
        print("Cache update complete")
