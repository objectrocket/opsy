import random
from datetime import datetime, timedelta
import click
from flask import current_app
from stevedore import extension
from opsy.config import ConfigOption
from opsy.exceptions import DuplicateError
from opsy.utils import print_notice, print_error
from opsy.plugins.base import BaseOpsyPlugin
from opsy.plugins.monitoring.access import needs
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
    needs = needs

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
                              'args': [zone.id, app]}
                if run_once:
                    job_kwargs['next_run_time'] = datetime.now()
                else:
                    next_run = datetime.now() + timedelta(
                        0, random.uniform(0, zone.interval))
                    job_args.append('interval')
                    job_kwargs['next_run_time'] = next_run
                    job_kwargs['seconds'] = zone.interval
                app.jobs.append([job_args, job_kwargs])

    def register_cli_commands(self, cli):

        @cli.group('monitoring')
        def monitoring_cli():
            """Commands related to the monitoring plugin."""
            pass

        @monitoring_cli.command('update-cache')
        # pylint: disable=unused-variable
        def update_monitoring_cache():
            """Update the monitoring cache."""
            from apscheduler.schedulers.background import BackgroundScheduler
            scheduler = BackgroundScheduler()
            self.register_scheduler_jobs(current_app, run_once=True)
            for args, kwargs in current_app.jobs:
                scheduler.add_job(*args, **kwargs)
            scheduler.start()
            while len(scheduler.get_jobs()) > 0:
                continue
            scheduler.shutdown(wait=True)

        @monitoring_cli.group('zone')
        def zone_cli():
            """Commands related to zones."""
            pass

        @zone_cli.command('create')
        @click.argument('name', type=click.STRING)
        @click.argument('backend', type=click.STRING)
        @click.option('--host', type=click.STRING)
        @click.option('--path', type=click.STRING)
        @click.option('--port', type=click.INT)
        @click.option('--timeout', type=click.INT)
        @click.option('--interval', type=click.INT)
        @click.option('--username', type=click.STRING)
        @click.option('--password', type=click.STRING)
        @click.option('--verify_ssl', type=click.BOOL)
        @click.option('--enabled', type=click.BOOL)
        # pylint: disable=unused-variable
        def zone_create(name, backend, **kwargs):
            """Create a zone."""
            zone_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            try:
                zone = Zone.create(name, backend, **zone_kwargs).pretty_print()
            except (DuplicateError, BackendNotFound) as error:
                print_error(error)

        @zone_cli.command('list')
        # pylint: disable=unused-variable
        def zone_list():
            """List all zones."""
            columns = ['id', 'name', 'backend', 'status', 'status_message',
                       'enabled', 'created_at', 'updated_at']
            Zone.query.pretty_list(columns)

        @zone_cli.command('show')
        @click.argument('zone_id_or_name', type=click.STRING)
        # pylint: disable=unused-variable
        def zone_show(zone_id_or_name):
            """Show a zone."""
            try:
                zone = Zone.get_by_id_or_name(zone_id_or_name).pretty_print()
            except ValueError as error:
                print_error(error)

        @zone_cli.command('delete')
        @click.argument('zone_id_or_name', type=click.STRING)
        # pylint: disable=unused-variable
        def zone_delete(zone_id_or_name):
            """Delete a zone."""
            try:
                Zone.delete_by_id_or_name(zone_id_or_name)
            except ValueError as error:
                print_error(error)
            print_notice('Zone "%s" deleted.' % zone_id_or_name)

        @zone_cli.command('modify')
        @click.argument('zone_id_or_name', type=click.STRING)
        @click.option('--name', type=click.STRING)
        @click.option('--host', type=click.STRING)
        @click.option('--path', type=click.STRING)
        @click.option('--port', type=click.INT)
        @click.option('--timeout', type=click.INT)
        @click.option('--interval', type=click.INT)
        @click.option('--username', type=click.STRING)
        @click.option('--password', type=click.STRING)
        @click.option('--verify_ssl', type=click.BOOL)
        @click.option('--enabled', type=click.BOOL)
        # pylint: disable=unused-variable
        def zone_modify(zone_id_or_name, **kwargs):
            """Modify a zone."""
            zone_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            try:
                zone = Zone.update_by_id_or_name(zone_id_or_name,
                                                 **zone_kwargs).pretty_print()
            except ValueError as error:
                print_error(error)

        @monitoring_cli.group('dashboard')
        def dashboard_cli():
            """Commands related to dashboards."""
            pass

        @dashboard_cli.command('create')
        @click.argument('name', type=click.STRING)
        @click.option('--description', type=click.STRING)
        @click.option('--enabled', type=click.BOOL)
        @click.option('--zone_filters', type=click.STRING)
        @click.option('--client_filters', type=click.STRING)
        @click.option('--check_filters', type=click.STRING)
        # pylint: disable=unused-variable
        def dashboard_create(name, **kwargs):
            """Create a dashboard."""
            dashboard_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            try:
                dashboard = Dashboard.create(name,
                                             **dashboard_kwargs).pretty_print(
                                                 ignore_attrs=['filters'])
            except DuplicateError as error:
                print_error(error)

        @dashboard_cli.command('list')
        # pylint: disable=unused-variable
        def dashboard_list():
            """List all dashboards."""
            columns = ['id', 'name', 'description', 'enabled', 'created_at',
                       'updated_at']
            Dashboard.query.pretty_list(columns)

        @dashboard_cli.command('show')
        @click.argument('dashboard_id_or_name', type=click.STRING)
        # pylint: disable=unused-variable
        def dashboard_show(dashboard_id_or_name):
            """Show a dashboard."""
            try:
                dashboard = Dashboard.get_by_id_or_name(
                    dashboard_id_or_name).pretty_print(ignore_attrs=['filters'])
            except ValueError as error:
                print_error(error)

        @dashboard_cli.command('delete')
        @click.argument('dashboard_id_or_name', type=click.STRING)
        # pylint: disable=unused-variable
        def dashboard_delete(dashboard_id_or_name):
            """Delete a dashboard."""
            try:
                Dashboard.delete_by_id_or_name(dashboard_id_or_name)
            except ValueError as error:
                print_error(error)
            print_notice('Dashboard "%s" deleted.' % dashboard_id_or_name)

        @dashboard_cli.command('modify')
        @click.argument('dashboard_id_or_name', type=click.STRING)
        @click.option('--name', type=click.STRING)
        @click.option('--description', type=click.STRING)
        @click.option('--enabled', type=click.BOOL)
        @click.option('--zone_filters', type=click.STRING)
        @click.option('--client_filters', type=click.STRING)
        @click.option('--check_filters', type=click.STRING)
        # pylint: disable=unused-variable
        def dashboard_modify(dashboard_id_or_name, **kwargs):
            """Modify a dashboard."""
            dashboard_kwargs = {k: v for k, v in kwargs.items()
                                if v is not None}
            try:
                dashboard = Dashboard.update_by_id_or_name(
                    dashboard_id_or_name,
                    **dashboard_kwargs).pretty_print(ignore_attrs=['filters'])
            except ValueError as error:
                print_error(error)

        @dashboard_cli.command('delete-filter')
        @click.argument('dashboard_id_or_name', type=click.STRING)
        @click.argument('entity_name', type=click.Choice(['client', 'check',
                                                          'zone']))
        # pylint: disable=unused-variable
        def dashboard_filter_delete(dashboard_id_or_name, entity_name):
            """Delete a dashboard's filter."""
            try:
                dashboard = Dashboard.get_by_id_or_name(dashboard_id_or_name)
                dashboard.delete_filter(entity_name)
            except ValueError as error:
                print_error(error)
            print_notice('Filter for entity "%s" for dashboard "%s" '
                         'deleted.' % (entity_name, dashboard_id_or_name))

        @dashboard_cli.command('test')
        @click.argument('dashboard_id_or_name', type=click.STRING)
        @click.argument('entity_name', type=click.Choice(
            ['client', 'check', 'result', 'event', 'silence', 'zone']))
        # pylint: disable=unused-variable
        def dashboard_test(dashboard_id_or_name, entity_name):
            """Test a dashboard."""
            entity = ENTITY_MAP[entity_name]
            try:
                dashboard = Dashboard.get_by_id_or_name(dashboard_id_or_name)
            except ValueError as error:
                print_error(error)
            filters_list = dashboard.get_filters_list(entity)
            for entity_object in entity.query.filter(*filters_list).all():
                print(entity_object)

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
