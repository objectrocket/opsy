import click
import random
from datetime import datetime, timedelta
from flask import current_app
from stevedore import extension
from opsy.utils import print_property_table
from opsy.plugins.base import BaseOpsyPlugin
from .api import monitoring_api
from .jobs import update_cache
from .main import monitoring_main
from .backends.base import Client, Check, Result, Event, Silence, Zone
from .dashboard import Dashboard, DashboardFilter
from .utils import ENTITY_MAP
from prettytable import PrettyTable


class MonitoringPlugin(BaseOpsyPlugin):
    """The monitoring dashboard plugin."""

    def __init__(self, app):
        # Load all available backends so sqlalchemy is aware of them.
        extension.ExtensionManager(namespace='opsy.monitoring.backend',
                                   invoke_on_load=False)

    def register_blueprints(self, app):
        app.register_blueprint(monitoring_main, url_prefix='/monitoring')
        app.register_blueprint(monitoring_api, url_prefix='/api/monitoring')

    def register_link_structure(self, app):

        def get_link(view, name, link_id, show_dashboards=False):
            with app.app_context():
                try:
                    dashboards = Dashboard.get_dashboards()
                except Exception:
                    dashboards = []
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
                        'name': dashboard,
                        'id': dashboard,
                        'content': view,
                        'get_vars': 'dashboard=%s' % dashboard,
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
            for zone in Zone.query.filter(Zone.enabled == 1).all():
                next_run = datetime.now() + timedelta(
                    0, random.uniform(0, zone.interval))
                if run_once:
                    app.jobs.append([[update_cache],
                                     {'id': 'monitoring_poller_%s' % zone.name,
                                      'next_run_time': datetime.now(),
                                      'max_instances': 1,
                                      'args': [zone, app.config_file]}])
                else:
                    app.jobs.append([[update_cache, 'interval'],
                                     {'id': 'monitoring_poller_%s' % zone.name,
                                      'next_run_time': next_run,
                                      'max_instances': 1,
                                      'seconds': zone.interval,
                                      'args': [zone, app.config_file]}])

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
            if Zone.get_zone_by_name(name):
                print('Zone "%s" already exists!' % name)
            else:
                Zone.create_zone(name, backend, **zone_kwargs)
                print('Zone "%s" created.' % name)

        @zone_cli.command('list')
        # pylint: disable=unused-variable
        def zone_list():
            """List all zones."""
            columns = ['id', 'name', 'backend', 'status', 'status_message',
                       'enabled', 'created_at', 'updated_at']
            table = PrettyTable(columns)
            for zone in Zone.get_zones():
                table.add_row([getattr(zone, x) for x in columns])
            print(table)

        @zone_cli.command('show')
        @click.argument('zone_id', type=click.UUID)
        # pylint: disable=unused-variable
        def zone_show(zone_id):
            """Show a zone."""
            zone = Zone.get_zone_by_id(zone_id)
            if zone:
                properties = [(x.key, getattr(zone, x.key))
                              for x in Zone.__table__.columns]
                print_property_table(properties)

        @zone_cli.command('delete')
        @click.argument('zone_id', type=click.UUID)
        # pylint: disable=unused-variable
        def zone_delete(zone_id):
            """Delete a zone."""
            Zone.delete_zone(zone_id)
            print('Zone "%s" deleted.' % zone_id)

        @zone_cli.command('modify')
        @click.argument('zone_id', type=click.UUID)
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
        def zone_modify(zone_id, **kwargs):
            """Modify a zone."""
            zone_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            if Zone.get_zone_by_id(zone_id):
                zone = Zone.update_zone(zone_id, **zone_kwargs)
                properties = [(x.key, getattr(zone, x.key))
                              for x in Zone.__table__.columns]
                print_property_table(properties)
            else:
                print('Could not find zone "%s"' % zone_id)

        @monitoring_cli.group('dashboard')
        def dashboard_cli():
            """Commands related to dashboards."""
            pass

        @dashboard_cli.command('create')
        @click.argument('name', type=click.STRING)
        @click.option('--description', type=click.STRING)
        @click.option('--enabled', type=click.BOOL)
        # pylint: disable=unused-variable
        def dashboard_create(name, **kwargs):
            """Create a dashboard."""
            dashboard_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            if Dashboard.get_dashboard_by_name(name):
                print('Dashboard "%s" already exists!' % name)
            else:
                dashboard = Dashboard.create_dashboard(name, **dashboard_kwargs)
                properties = [(x.key, getattr(dashboard, x.key))
                              for x in Dashboard.__table__.columns]
                print_property_table(properties)

        @dashboard_cli.command('list')
        # pylint: disable=unused-variable
        def dashboard_list():
            """List all dashboards."""
            columns = ['id', 'name', 'description', 'enabled', 'created_at',
                       'updated_at']
            table = PrettyTable(columns)
            for dashboard in Dashboard.get_dashboards():
                table.add_row([getattr(dashboard, x) for x in columns])
            print(table)

        @dashboard_cli.command('show')
        @click.argument('dashboard_id', type=click.UUID)
        # pylint: disable=unused-variable
        def dashboard_show(dashboard_id):
            """Show a dashboard."""
            dashboard = Dashboard.get_dashboard_by_id(dashboard_id)
            if dashboard:
                properties = [(x.key, getattr(dashboard, x.key))
                              for x in Dashboard.__table__.columns]
                print_property_table(properties)

        @dashboard_cli.command('delete')
        @click.argument('dashboard_id', type=click.UUID)
        # pylint: disable=unused-variable
        def dashboard_delete(dashboard_id):
            """Delete a dashboard."""
            Dashboard.delete_dashboard(dashboard_id)
            print('Dashboard "%s" deleted.' % dashboard_id)

        @dashboard_cli.command('modify')
        @click.argument('dashboard_id', type=click.UUID)
        @click.option('--name', type=click.STRING)
        @click.option('--description', type=click.STRING)
        @click.option('--enabled', type=click.BOOL)
        # pylint: disable=unused-variable
        def dashboard_modify(dashboard_id, **kwargs):
            """Modify a dashboard."""
            dashboard_kwargs = {k: v for k, v in kwargs.items()
                                if v is not None}
            if Dashboard.get_dashboard_by_id(dashboard_id):
                dashboard = Dashboard.update_dashboard(
                    dashboard_id, **dashboard_kwargs)
                properties = [(x.key, getattr(dashboard, x.key))
                              for x in Dashboard.__table__.columns]
                print_property_table(properties)
            else:
                print('Could not find dashboard "%s"' % dashboard_id)

        @dashboard_cli.command('test')
        @click.argument('dashboard_id', type=click.UUID)
        @click.argument('entity_name', type=click.Choice(
            ['client', 'check', 'result', 'event', 'silence', 'zone']))
        # pylint: disable=unused-variable
        def dashboard_test(dashboard_id, entity_name):
            """Test a dashboard."""
            entity = ENTITY_MAP[entity_name]
            dashboard = Dashboard.get_dashboard_by_id(dashboard_id)
            filters_list = dashboard.get_filters_list(entity)
            for entity_object in entity.query.filter(*filters_list).all():
                print(entity_object)

        @dashboard_cli.group('filter')
        def dashboard_filter_cli():
            """Commands related to dashboard filters."""
            pass

        @dashboard_filter_cli.command('create')
        @click.argument('dashboard_id', type=click.UUID)
        @click.argument('entity_name', type=click.Choice(['client', 'check',
                                                          'zone']))
        @click.argument('filters', type=click.STRING)
        # pylint: disable=unused-variable
        def dashboard_filter_create(dashboard_id, entity_name, filters):
            """Create a dashboard's filter."""
            dashboard = Dashboard.get_dashboard_by_id(dashboard_id)
            if not dashboard:
                print('Could not find dashboard "%s"' % dashboard_id)
            if dashboard.get_filter_by_entity(entity_name):
                print('A filter for entity "%s" already exists on '
                      'dashboard "%s".' % (entity_name, dashboard_id))
            dashboard.create_filter(entity_name, filters)

        @dashboard_filter_cli.command('list')
        @click.argument('dashboard_id', type=click.UUID)
        # pylint: disable=unused-variable
        def dashboard_filter_list(dashboard_id):  # pylint: disable=unused-variable
            """List a dashboard's filters."""
            dashboard = Dashboard.get_dashboard_by_id(dashboard_id)
            if not dashboard:
                print('Could not find dashboard "%s"' % dashboard_id)
                return
            columns = ['id', 'entity', 'filters', 'created_at', 'updated_at']
            table = PrettyTable(columns)
            for filter_object in dashboard.get_filters():
                table.add_row([getattr(filter_object, x) for x in columns])
            print(table)

        @dashboard_filter_cli.command('show')
        @click.argument('dashboard_id', type=click.UUID)
        @click.argument('entity_name', type=click.Choice(['client', 'check',
                                                          'zone']))
        # pylint: disable=unused-variable
        def dashboard_filter_show(dashboard_id, entity_name):
            """Show a dashboard's filters."""
            dashboard = Dashboard.get_dashboard_by_id(dashboard_id)
            if not dashboard:
                print('Could not find dashboard "%s"' % dashboard_id)
                return
            filter_object = dashboard.get_filter_by_entity(entity_name)
            if not filter_object:
                print('Could not find filter for entity "%s" for dashboard'
                      ' "%s"' % (entity_name, dashboard_id))
                return
            properties = [(x.key, getattr(filter_object, x.key))
                          for x in DashboardFilter.__table__.columns]
            print_property_table(properties)

        @dashboard_filter_cli.command('delete')
        @click.argument('dashboard_id', type=click.UUID)
        @click.argument('entity_name', type=click.Choice(['client', 'check',
                                                          'zone']))
        # pylint: disable=unused-variable
        def dashboard_filter_delete(dashboard_id, entity_name):
            """Delete a dashboard's filter."""
            dashboard = Dashboard.get_dashboard_by_id(dashboard_id)
            if not dashboard:
                print('Could not find dashboard "%s"' % dashboard_id)
                return
            dashboard.delete_filter(entity_name)
            print('Filter for entity "%s" for dashboard "%s" deleted.' % (
                  entity_name, dashboard_id))

        @dashboard_filter_cli.command('modify')
        @click.argument('dashboard_id', type=click.UUID)
        @click.argument('entity_name', type=click.Choice(['client', 'check',
                                                          'zone']))
        @click.argument('filters', type=click.STRING)
        # pylint: disable=unused-variable
        def dashboard_filter_modify(dashboard_id, entity_name, filters):
            """Modify a dashboard's filter."""
            dashboard = Dashboard.get_dashboard_by_id(dashboard_id)
            if not dashboard:
                print('Could not find dashboard "%s"' % dashboard_id)
                return
            dashboard.update_filter(entity_name, filters)
            print('Filter for entity "%s" for dashboard "%s" updated.' % (
                  entity_name, dashboard_id))

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
