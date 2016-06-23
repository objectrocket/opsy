import asyncio
from .cache import *
from . import db


class BasePlugin(object):
    zone_model = Zone
    models = [Check, Client, Event, Stash, Result]

    def __init__(self, name, host, port, timeout):
        self.zone = zone_model(name, host, port, timeout)
        db.session.add(self.zone)
        db.session.commit()

    def query_api(self, uri):
        raise NotImplementedError

    @asyncio.coroutine
    def update_objects(self, model):
        raise NotImplementedError

    def get_update_tasks(self, app, loop):
        tasks = []
        for model in self.models:
            tasks.append(asyncio.async(self.update_objects(app, loop, model)))
        return tasks

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.zone.name)
