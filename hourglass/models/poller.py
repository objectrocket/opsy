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
        self.interval = self.app.config.get('poll_interval', 10)

    @classmethod
    def get_clients(cls, sensu):
        return json.loads(requests.get('http://'+sensu['host']+':'+str(sensu['port'])+'/clients').content)

    @classmethod
    def get_checks(cls, sensu):
        return json.loads(requests.get('http://'+sensu['host']+':'+str(sensu['port'])+'/checks').content)

    @classmethod
    def get_events(cls, sensu):
        return json.loads(requests.get('http://'+sensu['host']+':'+str(sensu['port'])+'/events').content)

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
                        db.session.add(Client(sensu, client['name'], client['timestamp'], client))
                    except KeyError:
                        db.session.add(Client(sensu, client['name'], 0, client))
            db.session.commit()

    def update_events_cache(self, events):
        with self.app.app_context():
            Event.query.delete()
            for sensu in events:
                for event in events[sensu]:
                    db.session.add(Event(sensu, event['client']['name'], event['check']['name'], event['occurrences'], event['check']['status'], event['timestamp'], event))
            db.session.commit()

    def main(self):
        checks = {}
        clients = {}
        events = {}
        for sensu in self.sensus:
            checks[sensu] = self.get_checks(self.sensus[sensu])
            clients[sensu] = self.get_clients(self.sensus[sensu])
            events[sensu] = self.get_events(self.sensus[sensu])
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
