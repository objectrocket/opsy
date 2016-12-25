import os
from getpass import getpass
import click
from flask import current_app
from flask.cli import FlaskGroup, run_command
from prettytable import PrettyTable
from opsy.extensions import db
from opsy.app import create_app, create_scheduler
from opsy.exceptions import DuplicateError
from opsy.utils import load_plugins, print_error, print_notice
from opsy.auth.models import Role, User, Permission


DEFAULT_CONFIG = '%s/opsy.ini' % os.path.abspath(os.path.curdir)


def create_opsy_app(info):
    return create_app(os.environ.get('OPSY_CONFIG', DEFAULT_CONFIG))


cli = FlaskGroup(create_app=create_opsy_app,  # pylint: disable=invalid-name
                 add_default_commands=False,
                 help='The Opsy management cli.')
cli.add_command(run_command)


@cli.command('run-scheduler')
def run_scheduler():
    """Run the scheduler."""
    scheduler = create_scheduler(current_app)
    try:
        current_app.logger.info('Starting the scheduler...')
        scheduler.start()
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
                 'Permission': Permission}
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
def init_db():
    """Drop everything in database and rebuild the schema."""
    current_app.logger.info('Creating database...')
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.group('auth')
def auth_cli():
    """Commands related to auth."""
    pass


@auth_cli.command('permission-list')
# pylint: disable=unused-variable
def permission_list():
    """List all permissions the app is aware of."""
    needs_catalog = current_app.needs_catalog
    columns = ['name', 'description']
    print('\ncore app:')
    table = PrettyTable(columns, sortby='name')
    table.align['name'] = 'r'
    table.align['description'] = 'l'
    for name, need in current_app.needs_catalog.get('core').items():
        table.add_row([name, need.doc])
    print(table)
    needs_catalog.pop('core')
    for plugin in sorted(needs_catalog.keys()):
        print('\n%s plugin:' % plugin)
        table = PrettyTable(columns, sortby='name')
        table.align['name'] = 'r'
        table.align['description'] = 'l'
        for name, need in needs_catalog.get(plugin).items():
            table.add_row([name, need.doc])
        print(table)


@auth_cli.group('user')
def user_cli():
    """Commands related to users."""
    pass


@user_cli.command('create')
@click.argument('user_name', type=click.STRING)
@click.option('--full_name', type=click.STRING)
@click.option('--enabled', type=click.BOOL)
@click.option('--email', type=click.STRING)
@click.option('--password', type=click.STRING)
# pylint: disable=unused-variable
def user_create(user_name, **kwargs):
    """Create a user."""
    user_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        user = User.create(user_name, **user_kwargs).pretty_print()
    except DuplicateError as error:
        print_error(error)


@user_cli.command('password')
@click.argument('user_id_or_name', type=click.STRING)
# pylint: disable=unused-variable
def user_password(user_id_or_name):
    """Change a user's password interactively."""
    try:
        user = User.get_by_id_or_name(user_id_or_name, error_on_none=True)
    except ValueError as error:
        print_error(error)
    password1 = getpass('New password: ')
    password2 = getpass('New password again: ')
    if password1 != password2:
        print_error('Passwords do not match!')
    user.password = password1
    print_notice('Password updated for user "%s".' % user_id_or_name)


@user_cli.command('list')
# pylint: disable=unused-variable
def user_list():
    """List all users."""
    columns = ['id', 'name', 'full_name', 'email', 'enabled', 'created_at',
               'updated_at', 'roles']
    User.get().pretty_list(columns)


@user_cli.command('show')
@click.argument('user_id_or_name', type=click.STRING)
# pylint: disable=unused-variable
def user_show(user_id_or_name):
    """Show a user."""
    try:
        user = User.get_by_id_or_name(user_id_or_name,
                                      error_on_none=True).pretty_print()
    except ValueError as error:
        print_error(error)


@user_cli.command('delete')
@click.argument('user_id_or_name', type=click.STRING)
# pylint: disable=unused-variable
def user_delete(user_id_or_name):
    """Delete a user."""
    try:
        User.delete_by_id_or_name(user_id_or_name)
    except ValueError as error:
        print_error(error)
    print_notice('User "%s" deleted.' % user_id_or_name)


@user_cli.command('modify')
@click.argument('user_id_or_name', type=click.STRING)
@click.option('--enabled', type=click.BOOL)
@click.option('--name', type=click.STRING)
@click.option('--full_name', type=click.STRING)
@click.option('--email', type=click.STRING)
@click.option('--password', type=click.STRING)
# pylint: disable=unused-variable
def user_modify(user_id_or_name, **kwargs):
    """Modify a user."""
    user_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        user = User.update_by_id_or_name(user_id_or_name,
                                         **user_kwargs).pretty_print()
    except ValueError as error:
        print_error(error)


@user_cli.command('add-setting')
@click.argument('user_id_or_name', type=click.STRING)
@click.argument('key', type=click.STRING)
@click.argument('value', type=click.STRING)
# pylint: disable=unused-variable
def user_add_setting(user_id_or_name, key, value):
    """Add a setting to a user."""
    try:
        user = User.get_by_id_or_name(user_id_or_name, error_on_none=True)
    except ValueError as error:
        print_error(error)
    try:
        user.add_setting(key, value)
    except DuplicateError as error:
        print_error(error)
    user.pretty_print()


@user_cli.command('remove-setting')
@click.argument('user_id_or_name', type=click.STRING)
@click.argument('key', type=click.STRING)
# pylint: disable=unused-variable
def user_remove_setting(user_id_or_name, key):
    """Remove a user's setting."""
    try:
        user = User.get_by_id_or_name(user_id_or_name, error_on_none=True)
        user.remove_setting(key)
    except ValueError as error:
        print_error(error)
    user.pretty_print()


@user_cli.command('modify-setting')
@click.argument('user_id_or_name', type=click.STRING)
@click.argument('key', type=click.STRING)
@click.argument('value', type=click.STRING)
# pylint: disable=unused-variable
def user_modify_setting(user_id_or_name, key, value):
    """Modify a user's setting."""
    try:
        user = User.get_by_id_or_name(user_id_or_name, error_on_none=True)
        user.modify_setting(key)
    except ValueError as error:
        print_error(error)
    user.pretty_print()


@auth_cli.group('role')
def role_cli():
    """Commands related to roles."""
    pass


@role_cli.command('create')
@click.argument('role_name', type=click.STRING)
@click.option('--description', type=click.STRING)
# pylint: disable=unused-variable
def role_create(role_name, **kwargs):
    """Create a role."""
    role_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        role = Role.create(role_name, **role_kwargs).pretty_print()
    except DuplicateError as error:
        print_error(error)


@role_cli.command('list')
# pylint: disable=unused-variable
def role_list():
    """List all roles."""
    columns = ['id', 'name', 'description', 'created_at', 'updated_at']
    Role.get().pretty_list(columns)


@role_cli.command('show')
@click.argument('role_id_or_name', type=click.STRING)
# pylint: disable=unused-variable
def role_show(role_id_or_name):
    """Show a role."""
    try:
        role = Role.get_by_id_or_name(role_id_or_name,
                                      error_on_none=True).pretty_print()
    except ValueError as error:
        print_error(error)


@role_cli.command('delete')
@click.argument('role_id_or_name', type=click.STRING)
# pylint: disable=unused-variable
def role_delete(role_id_or_name):
    """Delete a role."""
    try:
        Role.delete_by_id_or_name(role_id_or_name)
    except ValueError as error:
        print_error(error)
    print_notice('Role "%s" deleted.' % role_id_or_name)


@role_cli.command('modify')
@click.argument('role_id_or_name', type=click.STRING)
@click.option('--description', type=click.STRING)
@click.option('--name', type=click.STRING)
# pylint: disable=unused-variable
def role_modify(role_id_or_name, **kwargs):
    """Modify a role."""
    role_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    try:
        role = Role.update_by_id_or_name(role_id_or_name,
                                         **role_kwargs).pretty_print()
    except ValueError as error:
        print_error(error)


@role_cli.command('add-user')
@click.argument('role_id_or_name', type=click.STRING)
@click.argument('user_id_or_name', type=click.STRING)
# pylint: disable=unused-variable
def role_add_user(role_id_or_name, user_id_or_name):
    """Add a user to a role."""
    try:
        user = User.get_by_id_or_name(user_id_or_name, error_on_none=True)
        role = Role.get_by_id_or_name(role_id_or_name, error_on_none=True)
        role.add_user(user)
    except ValueError as error:
        print_error(error)
    role.pretty_print()


@role_cli.command('remove-user')
@click.argument('role_id_or_name', type=click.STRING)
@click.argument('user_id_or_name', type=click.STRING)
# pylint: disable=unused-variable
def role_remove_user(role_id_or_name, user_id_or_name):
    """Remove a user from a role."""
    try:
        user = User.get_by_id_or_name(user_id_or_name, error_on_none=True)
        role = Role.get_by_id_or_name(role_id_or_name, error_on_none=True)
        role.remove_user(user)
    except ValueError as error:
        print_error(error)
    role.pretty_print()


@role_cli.command('add-permission')
@click.argument('role_id_or_name', type=click.STRING)
@click.argument('permission_name', type=click.STRING)
# pylint: disable=unused-variable
def role_add_permission(role_id_or_name, permission_name):
    """Add a permission to a role."""
    try:
        role = Role.get_by_id_or_name(role_id_or_name, error_on_none=True)
        role.add_permission(permission_name)
    except ValueError as error:
        print_error(error)
    role.pretty_print()


@role_cli.command('remove-permission')
@click.argument('role_id_or_name', type=click.STRING)
@click.argument('permission_name', type=click.STRING)
# pylint: disable=unused-variable
def role_remove_permission(role_id_or_name, permission_name):
    """Remove a permission from a role."""
    try:
        role = Role.get_by_id_or_name(role_id_or_name, error_on_none=True)
        role.remove_permission(permission_name)
    except ValueError as error:
        print_error(error)
    role.pretty_print()


def main():
    with create_opsy_app(None).app_context():
        for plugin in load_plugins(current_app):
            plugin.register_cli_commands(cli)
    cli()
