import asyncio
from stevedore import driver
from opsy.plugins.base import BaseOpsyPlugin
from opsy.db import db
from .api import monitoring_api
from .main import monitoring_main
from .backends.base import Zone
from opsy.exceptions import NoConfigSection
from datetime import datetime
from time import sleep
from _mysql_exceptions import OperationalError


class MonitoringPlugin(BaseOpsyPlugin):
    '''The monitoring dashboard plugin.'''

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
            enabled_zones = monitoring_config.get('enabled_zones', '').split(',')
            for zone in enabled_zones:
                monitoring_config['zones'][zone] = app.config[zone]
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
        '''Registers any blueprints that the plugin provides.

        :param app: Flask app object
        :type app: Flask
        :return: Flask app object
        :rtype: Flask
        '''
        app.register_blueprint(monitoring_main, url_prefix='/monitoring')
        app.register_blueprint(monitoring_api, url_prefix='/api/monitoring')

    def register_scheduler_jobs(self, app):
        '''Registers any scheduler jobs for the plugin.

        :param app: Flask app object
        :type app: Flask
        :return: List of apscheduler jobs
        :rtype: List of Jobs
        '''
        def update_cache(zone, config_file):
            from opsy.app import create_app
            from flask import current_app
            with create_app(config_file).app_context():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tasks = zone.get_update_tasks(current_app)
                results = loop.run_until_complete(asyncio.gather(*tasks))
                for result in results:
                    db.session.bulk_save_objects(result)
                try:
                    db.session.commit()
                except:
                    current_app.logger.error('Deadlock detected when updating %s, waiting one second.' % zone.name)
                    sleep(1)
                    db.session.commit()
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
        tasks = []
        for zone in self.zones:
            tasks.append([[update_cache, 'interval'],
                          {'next_run_time': datetime.now(),
                           'seconds': zone.interval,
                           'args': [zone, app.config_file]}])
        return tasks
