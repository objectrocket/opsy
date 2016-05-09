import gevent
import gevent.monkey
gevent.monkey.patch_all()
import requests

from time import time
from flask import json
from flask_sqlalchemy import SQLAlchemy

class Poller(object):
    def __init__(self, app):
        self.app = app
        self.db = SQLAlchemy(app)
        self.sensus = self.app.config['sensu_nodes']

    def get_events(self, sensu):
        return json.loads(requests.get('http://'+sensu['host']+':'+str(sensu['port'])+'/events').content)


    def store_events_cache(self, events):
        # TODO: Replace this with code that stores the events in the database
        print events[0]

    def main(self):
        events = []
        for sensu in self.sensus:
            events += self.get_events(self.sensus[sensu])
        self.store_events_cache(events)

    def run(self):
        while True:
            try:
                self.main()
                gevent.sleep(self.app.config.get('poll_interval', 10))
            except Exception as e:
                print(e)
