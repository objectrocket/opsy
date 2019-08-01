import asyncio
import os
from functools import partial, wraps
import click
from flask import current_app
from flask.cli import AppGroup, run_command, routes_command, ScriptInfo
from opsy.flask_extensions import db
from opsy.app import create_app, create_scheduler
from opsy.exceptions import DuplicateError
from opsy.utils import (load_plugins, print_error, print_notice,
                        get_protected_routes)
from opsy.auth.schema import UserSchema, RoleSchema, PermissionSchema
from opsy.auth.models import Role, User, Permission
from opsy.inventory.models import Zone, Host, Group, HostGroupMapping
from opsy.monitoring.models import Event, MonitoringService, Dashboard


DEFAULT_CONFIG = os.environ.get(
    'OPSY_CONFIG', '%s/opsy.ini' % os.path.abspath(os.path.curdir))

click_option = partial(  # pylint: disable=invalid-name
    click.option, show_default=True)


def common_params(func):
    @click_option('--json', type=click.BOOL, default=False, is_flag=True,
                  help='Output JSON')
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@click.group(cls=AppGroup, help='The Opsy management cli.')
@click_option('--config', type=click.Path(), default=DEFAULT_CONFIG,
              help='Config file for opsy.', show_default=True)
@click.pass_context
def cli(ctx, config):
    ctx.obj.data['config'] = config


cli.add_command(run_command)
cli.add_command(routes_command)


@cli.command('run-scheduler')
def run_scheduler():
    """Run the scheduler."""
    scheduler = create_scheduler(current_app)
    try:
        current_app.logger.info('Starting the scheduler...')
        scheduler.start()
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        current_app.logger.info('Stopping the scheduler...')


@cli.command('shell')
def shell():
    """Run a shell in the app context."""
    from flask.globals import _app_ctx_stack
    banner = 'Welcome to Opsy!'
    app = _app_ctx_stack.top.app
    shell_ctx = {'create_app': create_app,
                 'create_scheduler': create_scheduler,
                 'db': db,
                 'User': User,
                 'Role': Role,
                 'Permission': Permission,
                 'Zone': Zone,
                 'Host': Host,
                 'Group': Group,
                 'HostGroupMapping': HostGroupMapping,
                 'Event': Event,
                 'MonitoringService': MonitoringService,
                 'Dashboard': Dashboard}
    for plugin in load_plugins(current_app):
        plugin.register_shell_context(shell_ctx)
    shell_ctx.update(app.make_shell_context())
    try:
        from IPython import embed
        embed(user_ns=shell_ctx, banner1=banner)
        return
    except ImportError:
        import code
        code.interact(banner, local=shell_ctx)


@cli.command('init-db')
@click.confirmation_option(
    prompt='This will delete everything. Do you want to continue?')
def init_db():
    """Drop everything in database and rebuild the schema."""
    current_app.logger.info('Creating database...')
    db.drop_all()
    db.create_all()
    db.session.commit()


# @cli.group('auth')
# def auth_cli():
#     """Commands related to auth."""
#     pass


@cli.command('permission-list')
@click_option('--resource', type=click.STRING)
@click_option('--method', type=click.STRING)
@common_params
def permission_list(json, **kwargs):
    """List all permissions the app is aware of."""
    PermissionSchema(many=True).print(get_protected_routes(), json=json)


@cli.group('user')
def user_cli():
    """Commands related to users."""


@user_cli.command('create')
@click.argument('user_name', type=click.STRING)
@click_option('--full_name', type=click.STRING)
@click_option('--enabled', type=click.BOOL)
@click_option('--email', type=click.STRING)
@click_option('--password', type=click.STRING)
@common_params
def user_create(user_name, json=None, **kwargs):
    """Create a user."""
    user_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        UserSchema().print(User.create(user_name, **user_kwargs), json=json)
    except DuplicateError as error:
        print_error(error)


@user_cli.command('password')
@click.argument('user_id_or_name', type=click.STRING)
@click_option('--password', prompt=True, confirmation_prompt=True,
              hide_input=True)
def user_password(user_id_or_name, password):
    """Change a user's password interactively."""
    try:
        user = User.get_by_id_or_name(user_id_or_name, error_on_none=True)
    except ValueError as error:
        print_error(error)
    user.password = password
    print_notice('Password updated for user "%s".' % user_id_or_name)


@user_cli.command('list')
@common_params
def user_list(json):
    """List all users."""
    UserSchema(many=True).print(User.query, json=json)


@user_cli.command('show')
@click.argument('user_id_or_name', type=click.STRING)
@common_params
def user_show(user_id_or_name, json):
    """Show a user."""
    try:
        UserSchema().print(User.get_by_id_or_name(
            user_id_or_name, error_on_none=True), json=json)
    except ValueError as error:
        print_error(error)


@user_cli.command('delete')
@click.argument('user_id_or_name', type=click.STRING)
def user_delete(user_id_or_name):
    """Delete a user."""
    try:
        User.delete_by_id_or_name(user_id_or_name)
    except ValueError as error:
        print_error(error)
    print_notice('User "%s" deleted.' % user_id_or_name)


@user_cli.command('modify')
@click.argument('user_id_or_name', type=click.STRING)
@click_option('--enabled', type=click.BOOL)
@click_option('--name', type=click.STRING)
@click_option('--full_name', type=click.STRING)
@click_option('--email', type=click.STRING)
@click_option('--password', type=click.STRING)
@common_params
def user_modify(user_id_or_name, json=None, **kwargs):
    """Modify a user."""
    user_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        UserSchema().print(
            User.update_by_id_or_name(user_id_or_name, **user_kwargs),
            json=json)
    except ValueError as error:
        print_error(error)


@user_cli.command('add-setting')
@click.argument('user_id_or_name', type=click.STRING)
@click.argument('key', type=click.STRING)
@click.argument('value', type=click.STRING)
@common_params
def user_add_setting(user_id_or_name, key, value, json=None):
    """Add a setting to a user."""
    try:
        user = User.get_by_id_or_name(user_id_or_name, error_on_none=True)
    except ValueError as error:
        print_error(error)
    try:
        user.add_setting(key, value)
    except DuplicateError as error:
        print_error(error)
    UserSchema().print(user, json=json)


@user_cli.command('remove-setting')
@click.argument('user_id_or_name', type=click.STRING)
@click.argument('key', type=click.STRING)
@common_params
def user_remove_setting(user_id_or_name, key, json):
    """Remove a user's setting."""
    try:
        user = User.get_by_id_or_name(user_id_or_name, error_on_none=True)
        user.remove_setting(key)
    except ValueError as error:
        print_error(error)
    UserSchema().print(user, json=json)


@user_cli.command('modify-setting')
@click.argument('user_id_or_name', type=click.STRING)
@click.argument('key', type=click.STRING)
@click.argument('value', type=click.STRING)
@common_params
def user_modify_setting(user_id_or_name, key, value, json):
    """Modify a user's setting."""
    try:
        user = User.get_by_id_or_name(user_id_or_name, error_on_none=True)
        user.modify_setting(key)
    except ValueError as error:
        print_error(error)
    UserSchema().print(user, json=json)


@cli.group('role')
def role_cli():
    """Commands related to roles."""


@role_cli.command('create')
@click.argument('role_name', type=click.STRING)
@click_option('--ldap_group', type=click.STRING)
@click_option('--description', type=click.STRING)
@common_params
def role_create(role_name, json=None, **kwargs):
    """Create a role."""
    role_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        RoleSchema().print(Role.create(role_name, **role_kwargs), json=json)
    except DuplicateError as error:
        print_error(error)


@role_cli.command('list')
@common_params
def role_list(json):
    """List all roles."""
    RoleSchema(many=True).print(Role.query, json=json)


@role_cli.command('show')
@click.argument('role_id_or_name', type=click.STRING)
@common_params
def role_show(role_id_or_name, json):
    """Show a role."""
    try:
        RoleSchema().print(Role.get_by_id_or_name(
            role_id_or_name, error_on_none=True), json=json)
    except ValueError as error:
        print_error(error)


@role_cli.command('delete')
@click.argument('role_id_or_name', type=click.STRING)
def role_delete(role_id_or_name):
    """Delete a role."""
    try:
        Role.delete_by_id_or_name(role_id_or_name)
    except ValueError as error:
        print_error(error)
    print_notice('Role "%s" deleted.' % role_id_or_name)


@role_cli.command('modify')
@click.argument('role_id_or_name', type=click.STRING)
@click_option('--description', type=click.STRING)
@click_option('--ldap_group', type=click.STRING)
@click_option('--name', type=click.STRING)
@common_params
def role_modify(role_id_or_name, json=None, **kwargs):
    """Modify a role."""
    role_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        RoleSchema().print(Role.update_by_id_or_name(
            role_id_or_name, **role_kwargs), json=json)
    except ValueError as error:
        print_error(error)


@role_cli.command('add-user')
@click.argument('role_id_or_name', type=click.STRING)
@click.argument('user_ids_or_names', type=click.STRING, nargs=-1)
@common_params
def role_add_user(role_id_or_name, user_ids_or_names, json):
    """Add a users to a role."""
    try:
        role = Role.get_by_id_or_name(role_id_or_name, error_on_none=True)
        for user_id_or_name in user_ids_or_names:
            user = User.get_by_id_or_name(user_id_or_name,
                                          error_on_none=True)
            role.add_user(user)
    except ValueError as error:
        print_error(error)
    RoleSchema().print(role)


@role_cli.command('remove-user')
@click.argument('role_id_or_name', type=click.STRING)
@click.argument('user_ids_or_names', type=click.STRING, nargs=-1)
@common_params
def role_remove_user(role_id_or_name, user_ids_or_names, json):
    """Remove a users from a role."""
    try:
        role = Role.get_by_id_or_name(role_id_or_name, error_on_none=True)
        for user_id_or_name in user_ids_or_names:
            user = User.get_by_id_or_name(user_id_or_name,
                                          error_on_none=True)
            role.remove_user(user)
    except ValueError as error:
        print_error(error)
    RoleSchema().print(role)


@role_cli.command('add-permission')
@click.argument('role_id_or_name', type=click.STRING)
@click.argument('permission_names', type=click.STRING, nargs=-1)
@common_params
def role_add_permission(role_id_or_name, permission_names, json):
    """Add a permissions to a role."""
    try:
        role = Role.get_by_id_or_name(role_id_or_name, error_on_none=True)
        for permission_name in permission_names:
            role.add_permission(permission_name)
    except ValueError as error:
        print_error(error)
    RoleSchema().print(role, json=json)


@role_cli.command('remove-permission')
@click.argument('role_id_or_name', type=click.STRING)
@click.argument('permission_names', type=click.STRING, nargs=-1)
@common_params
def role_remove_permission(role_id_or_name, permission_names, json):
    """Remove a permissions from a role."""
    try:
        role = Role.get_by_id_or_name(role_id_or_name, error_on_none=True)
        for permission_name in permission_names:
            role.remove_permission(permission_name)
    except ValueError as error:
        print_error(error)
    RoleSchema().print(role, json=json)


def main():

    def create_opsy_app(script_info):
        return create_app(script_info.data['config'])
    # Load the plugins
    #extension.ExtensionManager(namespace='opsy.command', invoke_on_load=False)
    cli(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
        obj=ScriptInfo(create_app=create_opsy_app))
