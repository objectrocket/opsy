import gevent
import gevent.monkey
import requests
from flask import json
from hourglass.models.api import Check, Client, Event
from . import db

gevent.monkey.patch_all()


class Poller(object):
    def __init__(self, app):
        self.app = app
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            db.session.commit()
        self.sensus = self.app.config['sensu_nodes']
        self.interval = self.app.config['hourglass'].get('poll_interval', 10)

    @classmethod
    def query_sensu(cls, sensu, uri):
        url = "http://%s:%s/%s" % (sensu['host'], sensu['port'], uri)
        return json.loads(requests.get(url).content)

    def update_checks_cache(self, checks):
        with self.app.app_context():
            Check.query.delete()
            for sensu in checks:
                for check in checks[sensu]:
                    db.session.add(Check(sensu, check['name'], check))
            db.session.commit()

    def update_clients_cache(self, clients):
        with self.app.app_context():
            Client.query.delete()
            for sensu in clients:
                for client in clients[sensu]:
                    try:
                        db.session.add(Client(sensu, client['name'], client, client['timestamp']))
                    except KeyError:
                        db.session.add(Client(sensu, client['name'], client))
            db.session.commit()

    def update_events_cache(self, events):
        with self.app.app_context():
            Event.query.delete()
            for sensu in events:
                for event in events[sensu]:
                    db.session.add(Event(sensu, event['client']['name'], event['occurrences'], event['check']['status'], event['timestamp'], event))
            db.session.commit()

    def main(self):
        self.app.logger.debug('Updating Cache')
        checks = {}
        clients = {}
        events = {}
        for sensu in self.sensus:
            checks[sensu] = self.query_sensu(self.sensus[sensu], 'checks')
            clients[sensu] = self.query_sensu(self.sensus[sensu], 'clients')
            events[sensu] = self.query_sensu(self.sensus[sensu], 'events')
        self.update_clients_cache(clients)
        self.update_checks_cache(checks)
        self.update_events_cache(events)

    def run(self):
        while True:
            try:
                self.main()
                gevent.sleep(self.interval)
            except Exception:
                raise
