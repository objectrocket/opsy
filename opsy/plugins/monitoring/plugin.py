import asyncio
from datetime import datetime
from stevedore import driver
from flask_script import Command
from sqlalchemy.exc import OperationalError
from opsy.exceptions import NoConfigSection
from opsy.plugins.base import BaseOpsyPlugin
from opsy.db import db
from .api import monitoring_api
from .main import monitoring_main
from .backends.base import Client, Check, Result, Event, Silence, Zone


class MonitoringPlugin(BaseOpsyPlugin):
    """The monitoring dashboard plugin."""

    def __init__(self, app):
        self.config = app.config.get('monitoring')
        if self.config is None:
            raise NoConfigSection('Config section "monitoring" does not exist')
        self._parse_config(app)
        self.zones = []
        for name, zone_config in self.config['zones'].items():
            backend = zone_config.get('backend')
            backend_manager = driver.DriverManager(
                namespace='opsy.monitoring.backend',
                name=backend,
                invoke_on_load=True,
                invoke_args=(name,),
                invoke_kwds=(zone_config))
            self.zones.append(backend_manager.driver)

    def _parse_config(self, app):
        monitoring_config = app.config.get('monitoring')
        if monitoring_config is None:
            raise NoConfigSection('Config section "monitoring" does not exist')
        monitoring_config['zones'] = {}
        monitoring_config['dashboards'] = {}
        if monitoring_config.get('enabled_zones'):
            enabled_zones = monitoring_config.get(
                'enabled_zones', '').split(',')
            for zone in enabled_zones:
                try:
                    monitoring_config['zones'][zone] = app.config[zone]
                except KeyError:
                    app.logger.error('Config section for zone "%s" does not '
                                     'exist. Skipping.' % zone)
        if monitoring_config.get('enabled_dashboards'):
            enabled_dashboards = monitoring_config.get(
                'enabled_dashboards').split(',')
            for dashboard in enabled_dashboards:
                if app.config.get(dashboard):
                    monitoring_config['dashboards'][dashboard] = {}
                    dash_config = monitoring_config['dashboards'][dashboard]
                    dash_config['zone'] = app.config[dashboard].get('zone')
                    dash_config['check'] = app.config[dashboard].get('check')
                    dash_config['check'] = app.config[dashboard].get('check')
                else:
                    raise NoConfigSection('Config section "%s" does not exist'
                                          % dashboard)

    def register_blueprints(self, app):
        app.register_blueprint(monitoring_main, url_prefix='/monitoring')
        app.register_blueprint(monitoring_api, url_prefix='/api/monitoring')

    def register_scheduler_jobs(self, app):
        def update_cache(zone, config_file):
            from opsy.app import create_app
            from flask import current_app
            with create_app(config_file).app_context():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tasks = zone.get_update_tasks(current_app)
                results = loop.run_until_complete(asyncio.gather(*tasks))
                for del_objects, init_objects in results:
                    for i in range(3):  # three retries for deadlocks
                        try:
                            if del_objects:
                                del_objects.delete()
                            db.session.bulk_save_objects(init_objects)
                            db.session.commit()
                        except OperationalError as e:  # pylint: disable=invalid-name
                            if i == (3 - 1):
                                raise
                            current_app.logger.info(
                                'Retryable error in transaction on '
                                'attempt %d for zone %s. %s: %s',
                                i + 1, zone.name, e.__class__.__name__, e)
                            db.session.rollback()  # pylint: disable=no-member
                current_app.logger.info('Cache updated for %s' % zone.name)
        # Create the db object for the zones.
        with app.app_context():
            for zone in Zone.query.all():
                zone.delete_cache(app)
            Zone.query.delete()
            db.session.bulk_save_objects(self.zones)
            for zone in self.zones:
                db.session.bulk_save_objects(zone.create_poller_metadata(app))
            db.session.commit()
        jobs = []
        for zone in self.zones:
            jobs.append([[update_cache, 'interval'],
                         {'next_run_time': datetime.now(),
                          'max_instances': 1,
                          'seconds': zone.interval,
                          'args': [zone, app.config_file]}])
        return jobs

    @classmethod
    def get_cli_commands(cls):
        print('blahblah')
        class UpdateCache(Command):
            "Test"

            def run(self):
                print('test')
        return [('updatecache', UpdateCache())]

    def register_shell_objects(self, shell_vars):
        monitoring_vars = {'Client': Client,
                           'Check': Check,
                           'Result': Result,
                           'Event': Event,
                           'Silence': Silence,
                           'Zone': Zone}
        return shell_vars.update(monitoring_vars)
