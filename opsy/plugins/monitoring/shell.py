import click
from flask import current_app
from opsy.shell import cli, click_option, common_params
from opsy.exceptions import DuplicateError
from opsy.utils import print_notice, print_error
from opsy.plugins.monitoring import MonitoringPlugin
from opsy.plugins.monitoring.backends.base import Zone
from opsy.plugins.monitoring.dashboard import Dashboard
from opsy.plugins.monitoring.exceptions import BackendNotFound
from opsy.plugins.monitoring.schema import ZoneSchema, DashboardSchema


@cli.group('monitoring')
def monitoring_cli():
    """Commands related to the monitoring plugin."""


@monitoring_cli.command('update-cache')
def update_monitoring_cache():
    """Update the monitoring cache."""
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    MonitoringPlugin(current_app).register_scheduler_jobs(
        current_app, run_once=True)
    for args, kwargs in current_app.jobs:
        scheduler.add_job(*args, **kwargs)
    scheduler.start()
    while scheduler.get_jobs():
        continue
    scheduler.shutdown(wait=True)


@monitoring_cli.group('zone')
def zone_cli():
    """Commands related to zones."""


@zone_cli.command('create')
@click.argument('name', type=click.STRING)
@click.argument('backend', type=click.STRING)
@click_option('--host', type=click.STRING)
@click_option('--path', type=click.STRING)
@click_option('--port', type=click.INT)
@click_option('--timeout', type=click.INT)
@click_option('--interval', type=click.INT)
@click_option('--username', type=click.STRING)
@click_option('--password', type=click.STRING)
@click_option('--verify_ssl', type=click.BOOL)
@click_option('--enabled', type=click.BOOL)
@common_params
def zone_create(name, backend, json=None, **kwargs):
    """Create a zone."""
    zone_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        ZoneSchema().print(
            Zone.create(name, backend, **zone_kwargs), json=json)
    except (DuplicateError, BackendNotFound) as error:
        print_error(error)


@zone_cli.command('list')
@common_params
def zone_list(json):
    """List all zones."""
    columns = ['id', 'name', 'backend', 'status', 'status_message',
               'enabled', 'created_at', 'updated_at']
    ZoneSchema(many=True, only=columns).print(Zone.query, json=json)


@zone_cli.command('show')
@click.argument('zone_id_or_name', type=click.STRING)
@common_params
def zone_show(zone_id_or_name, json):
    """Show a zone."""
    try:
        ZoneSchema().print(
            Zone.get_by_id_or_name(zone_id_or_name), json=json)
    except ValueError as error:
        print_error(error)


@zone_cli.command('delete')
@click.argument('zone_id_or_name', type=click.STRING)
def zone_delete(zone_id_or_name):
    """Delete a zone."""
    try:
        Zone.delete_by_id_or_name(zone_id_or_name)
    except ValueError as error:
        print_error(error)
    print_notice('Zone "%s" deleted.' % zone_id_or_name)


@zone_cli.command('modify')
@click.argument('zone_id_or_name', type=click.STRING)
@click_option('--name', type=click.STRING)
@click_option('--host', type=click.STRING)
@click_option('--path', type=click.STRING)
@click_option('--port', type=click.INT)
@click_option('--timeout', type=click.INT)
@click_option('--interval', type=click.INT)
@click_option('--username', type=click.STRING)
@click_option('--password', type=click.STRING)
@click_option('--verify_ssl', type=click.BOOL)
@click_option('--enabled', type=click.BOOL)
@common_params
def zone_modify(zone_id_or_name, json=None, **kwargs):
    """Modify a zone."""
    zone_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        ZoneSchema().print(
            Zone.update_by_id_or_name(zone_id_or_name, **zone_kwargs),
            json=json)
    except ValueError as error:
        print_error(error)


@monitoring_cli.group('dashboard')
def dashboard_cli():
    """Commands related to dashboards."""


@dashboard_cli.command('create')
@click.argument('name', type=click.STRING)
@click_option('--description', type=click.STRING)
@click_option('--enabled', type=click.BOOL)
@click_option('--zone_filters', type=click.STRING)
@click_option('--client_filters', type=click.STRING)
@click_option('--check_filters', type=click.STRING)
@common_params
def dashboard_create(name, json=None, **kwargs):
    """Create a dashboard."""
    dashboard_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        DashboardSchema().print(
            Dashboard.create(name, **dashboard_kwargs), json=json)
    except DuplicateError as error:
        print_error(error)


@dashboard_cli.command('list')
@common_params
def dashboard_list(json):
    """List all dashboards."""
    DashboardSchema(many=True).print(Dashboard.query)


@dashboard_cli.command('show')
@click.argument('dashboard_id_or_name', type=click.STRING)
@common_params
def dashboard_show(dashboard_id_or_name, json):
    """Show a dashboard."""
    try:
        DashboardSchema().print(
            Dashboard.get_by_id_or_name(dashboard_id_or_name), json=json)
    except ValueError as error:
        print_error(error)


@dashboard_cli.command('delete')
@click.argument('dashboard_id_or_name', type=click.STRING)
def dashboard_delete(dashboard_id_or_name):
    """Delete a dashboard."""
    try:
        Dashboard.delete_by_id_or_name(dashboard_id_or_name)
    except ValueError as error:
        print_error(error)
    print_notice('Dashboard "%s" deleted.' % dashboard_id_or_name)


@dashboard_cli.command('modify')
@click.argument('dashboard_id_or_name', type=click.STRING)
@click_option('--name', type=click.STRING)
@click_option('--description', type=click.STRING)
@click_option('--enabled', type=click.BOOL)
@click_option('--zone_filters', type=click.STRING)
@click_option('--client_filters', type=click.STRING)
@click_option('--check_filters', type=click.STRING)
@common_params
def dashboard_modify(dashboard_id_or_name, json=None, **kwargs):
    """Modify a dashboard."""
    dashboard_kwargs = {k: v for k, v in kwargs.items()
                        if v is not None}
    try:
        DashboardSchema().print(
            Dashboard.update_by_id_or_name(
                dashboard_id_or_name, **dashboard_kwargs), json=json)
    except ValueError as error:
        print_error(error)


@dashboard_cli.command('delete-filter')
@click.argument('dashboard_id_or_name', type=click.STRING)
@click.argument('entity_name', type=click.Choice(['client', 'check', 'zone']))
def dashboard_filter_delete(dashboard_id_or_name, entity_name):
    """Delete a dashboard's filter."""
    try:
        dashboard = Dashboard.get_by_id_or_name(dashboard_id_or_name)
        dashboard.delete_filter(entity_name)
    except ValueError as error:
        print_error(error)
    print_notice('Filter for entity "%s" for dashboard "%s" '
                 'deleted.' % (entity_name, dashboard_id_or_name))
