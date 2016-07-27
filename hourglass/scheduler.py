import asyncio
import importlib
from hourglass.db import db
from hourglass.backends.cache import Zone
from hourglass.app import create_app
from flask import current_app


class Scheduler(object):

    def __init__(self, config_file):
        self.loop = asyncio.get_event_loop()
        self.config_file = config_file
        with create_app(self.config_file).app_context():
            self.config = current_app.config
            self.interval = int(current_app.config['hourglass'].get(
                'scheduler_interval', 30))

    def _load_zones(self):
        zones = []
        for name, config in self.config['zones'].items():
            backend = config.get('backend')
            package = backend.split(':')[0]
            class_name = backend.split(':')[1]
            zone_module = importlib.import_module(package)
            zone_class = getattr(zone_module, class_name)
            zones.append(zone_class(name, **config))
        return zones

    def create_cache_db(self):
        self._load_zones()
        with create_app(self.config_file).app_context():
            current_app.logger.info('Creating cache database')
            db.drop_all(bind='cache')
            db.create_all(bind='cache')
            zones = self._load_zones()
            db.session.bulk_save_objects(zones)
            db.session.commit()

    def run_tasks(self):
        with create_app(self.config_file).app_context():
            tasks = []
            for zone in Zone.query.all():
                tasks.extend(zone.get_update_tasks(current_app))
            results = self.loop.run_until_complete(asyncio.gather(*tasks))
            for result in results:
                db.session.bulk_save_objects(result)
            db.session.commit()
            current_app.logger.info('Cache database updated')
