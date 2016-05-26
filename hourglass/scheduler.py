import asyncio
import importlib
from hourglass.backends import db


class UwsgiScheduler(object):

    def __init__(self, app):
        self.app = app
        self.loop = asyncio.get_event_loop()
        self.interval = int(app.config['hourglass'].get(
            'scheduler_interval', 30))
        self.pollers = self._load_pollers()

    def _load_pollers(self):
        pollers = []
        for name, config in self.app.config['sources'].items():
            backend = config.get('backend')
            package = backend.split(':')[0]
            class_name = backend.split(':')[1]
            poller_module = importlib.import_module(package)
            poller_class = getattr(poller_module, class_name)
            pollers.append(poller_class(self.app, self.loop, name, config))
        return pollers

    def run_tasks(self):
        with self.app.app_context():
            tasks = []
            for poller in self.pollers:
                tasks.extend(poller.get_update_tasks())
            results = self.loop.run_until_complete(asyncio.gather(*tasks))
            for result in results:
                db.session.bulk_save_objects(result)
            db.session.commit()
            self.app.logger.info('Cache database updated')
