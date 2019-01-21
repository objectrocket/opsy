import random
from datetime import datetime, timedelta
import click
from flask import current_app
from stevedore import extension
from opsy.config import ConfigOption
from opsy.exceptions import DuplicateError
from opsy.utils import print_notice, print_error
from opsy.plugins.base import BaseOpsyPlugin
from opsy.plugins.monitoring.access import monitoring_needs
from opsy.plugins.monitoring.api import monitoring_api
from opsy.plugins.monitoring.jobs import update_cache
from opsy.plugins.monitoring.main import monitoring_main
from opsy.plugins.monitoring.backends.base import Client, Check, Result, \
    Event, Silence, Zone
from opsy.plugins.monitoring.dashboard import Dashboard, DashboardFilter
from opsy.plugins.monitoring.utils import ENTITY_MAP
from opsy.plugins.monitoring.exceptions import BackendNotFound


class MonitoringPlugin(BaseOpsyPlugin):
    """The monitoring dashboard plugin."""

    def __init__(self, app):
        # Load all available backends so sqlalchemy is aware of them.
        extension.ExtensionManager(namespace='opsy.monitoring.backend',
                                   invoke_on_load=False)

    name = 'monitoring'
    config_options = [
        ConfigOption('uchiwa_url', str, False, None)
    ]
    needs = monitoring_needs

    def register_blueprints(self, app):
        app.register_blueprint(monitoring_main, url_prefix='/monitoring')
        app.register_blueprint(
            monitoring_api, url_prefix='/api/plugins/monitoring')

    def register_link_structure(self, app):  # pylint: disable=R0201

        def get_link(view, name, link_id, show_dashboards=False):
            with app.app_context():
                dashboards = Dashboard.query.all()
            if show_dashboards:
                dropdown_links = [
                    {
                        'name': 'All %s' % name,
                        'id': 'all_%s' % link_id,
                        'content': view,
                        'get_vars': None,
                        'type': 'link'
                    },
                    {'type': 'divider'},
                    {'type': 'header', 'name': 'Dashboards'}
                ]
                dropdown_links.extend([
                    {
                        'name': dashboard.name,
                        'id': dashboard.name,
                        'content': view,
                        'get_vars': 'dashboard=%s' % dashboard.name,
                        'type': 'link'
                    } for dashboard in dashboards])
                link = {
                    'name': name,
                    'id': link_id,
                    'content': dropdown_links,
                    'type': 'dropdown'
                }
            else:
                link = {
                    'name': name,
                    'id': link_id,
                    'content': view,
                    'get_vars': None,
                    'type': 'link'
                }
            return link

        links = [
            get_link('monitoring_main.events',
                     'Events', 'events', show_dashboards=True),
            get_link('monitoring_main.checks', 'Checks', 'checks'),
            get_link('monitoring_main.clients', 'Clients', 'clients')
        ]
        app.plugin_links.extend(links)

    def register_scheduler_jobs(self, app, run_once=False):
        with app.app_context():
            zones = Zone.query.filter(Zone.enabled == 1).all()
        for zone in zones:
            job_args = [update_cache]
            job_kwargs = {'id': 'monitoring_poller_%s' % zone.name,
                          'next_run_time': datetime.now(),
                          'max_instances': 1,
                          'args': [zone.id, app.config_file]}
            if run_once:
                job_kwargs['next_run_time'] = datetime.now()
            else:
                next_run = datetime.now() + timedelta(
                    0, random.uniform(0, zone.interval))
                job_args.append('interval')
                job_kwargs['next_run_time'] = next_run
                job_kwargs['seconds'] = zone.interval
            app.jobs.append([job_args, job_kwargs])

    def register_shell_context(self, shell_ctx):
        monitoring_ctx = {'Client': Client,
                          'Check': Check,
                          'Result': Result,
                          'Event': Event,
                          'Silence': Silence,
                          'Zone': Zone,
                          'Dashboard': Dashboard,
                          'DashboardFilter': DashboardFilter}
        shell_ctx.update(monitoring_ctx)
