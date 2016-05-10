import gevent
import gevent.monkey
import requests
from flask import json
from hourglass.models.api import Client
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

    def update_clients_cache(self, clients):
        with self.app.app_context():
            Client.query.delete()
            for sensu in clients:
                for client in clients[sensu]:
                    try:
                        db.session.add(Client(sensu, client['name'], client, client['timestamp']))
                    except KeyError:
                        db.session.add(Client(sensu, client['name'], client, 0))
            db.session.commit()

    def main(self):
        clients = {}
        for sensu in self.sensus:
            clients[sensu] = self.get_clients(self.sensus[sensu])
        self.update_clients_cache(clients)

    def run(self):
        while True:
            try:
                self.main()
                gevent.sleep(self.interval)
            except Exception:
                raise
