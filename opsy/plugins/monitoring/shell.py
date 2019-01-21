import click
# from flask import current_app
from opsy.shell import cli, click_option
from opsy.exceptions import DuplicateError
from opsy.utils import print_notice, print_error
from opsy.plugins.monitoring.backends.base import Zone
from opsy.plugins.monitoring.dashboard import Dashboard
from opsy.plugins.monitoring.utils import ENTITY_MAP
from opsy.plugins.monitoring.exceptions import BackendNotFound


@cli.group('monitoring')
def monitoring_cli():
    """Commands related to the monitoring plugin."""


# @monitoring_cli.command('update-cache')
# def update_monitoring_cache():
#     """Update the monitoring cache."""
#     from apscheduler.schedulers.background import BackgroundScheduler
#     scheduler = BackgroundScheduler()
#     self.register_scheduler_jobs(current_app, run_once=True)
#     for args, kwargs in current_app.jobs:
#         scheduler.add_job(*args, **kwargs)
#     scheduler.start()
#     while scheduler.get_jobs():
#         continue
#     scheduler.shutdown(wait=True)


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
def zone_create(name, backend, **kwargs):
    """Create a zone."""
    zone_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        Zone.create(name, backend, **zone_kwargs).pretty_print()
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
        Zone.get_by_id_or_name(zone_id_or_name).pretty_print()
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
# pylint: disable=unused-variable
def zone_modify(zone_id_or_name, **kwargs):
    """Modify a zone."""
    zone_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        Zone.update_by_id_or_name(zone_id_or_name,
                                  **zone_kwargs).pretty_print()
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
# pylint: disable=unused-variable
def dashboard_create(name, **kwargs):
    """Create a dashboard."""
    dashboard_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        Dashboard.create(name, **dashboard_kwargs).pretty_print(
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
        Dashboard.get_by_id_or_name(
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
@click_option('--name', type=click.STRING)
@click_option('--description', type=click.STRING)
@click_option('--enabled', type=click.BOOL)
@click_option('--zone_filters', type=click.STRING)
@click_option('--client_filters', type=click.STRING)
@click_option('--check_filters', type=click.STRING)
# pylint: disable=unused-variable
def dashboard_modify(dashboard_id_or_name, **kwargs):
    """Modify a dashboard."""
    dashboard_kwargs = {k: v for k, v in kwargs.items()
                        if v is not None}
    try:
        Dashboard.update_by_id_or_name(
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
