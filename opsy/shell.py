import os
import sys
from functools import partial
import click
from flask import current_app
from flask.cli import (
    AppGroup, routes_command, ScriptInfo, with_appcontext, pass_script_info)
from flask_migrate.cli import db as db_command

import opsy
from opsy.flask_extensions import db
from opsy.app import create_app
from opsy.config import load_config
from opsy.exceptions import NoConfigFile
from opsy.server import create_server
from opsy.auth.schema import AppPermissionSchema, UserSchema, RoleSchema
from opsy.utils import (
    print_error, print_notice, get_protected_routes, get_valid_permissions)
from opsy.auth.models import Role, User, Permission
from opsy.inventory.models import Zone, Host, Group, HostGroupMapping


click_option = partial(  # pylint: disable=invalid-name
    click.option, show_default=True, show_envvar=True)


@click.group(cls=AppGroup, help='The Opsy management cli.')
@click_option('--config', type=click.Path(),
              default=f'{os.path.abspath(os.path.curdir)}/opsy.toml',
              envvar='OPSY_CONFIG', help='Config file for opsy.')
@click_option('--app_database_uri', type=click.STRING,
              envvar='OPSY_APP_DATABASE_URI',
              help='The SQLAlchemy compatible database URI')
@click_option('--app_secret_key', type=click.STRING,
              envvar='OPSY_APP_SECRET_KEY',
              help='The key used for crypto features.')
@click_option('--app_uri_prefix', type=click.STRING,
              envvar='OPSY_APP_URI_PREFIX',
              help='URL prefix if mounted behind a reverse proxy.')
@click_option('--server_host', type=click.STRING,
              envvar='OPSY_SERVER_HOST',
              help='Host address.')
@click_option('--server_port', type=click.INT,
              envvar='OPSY_SERVER_PORT',
              help='Port number to listen on.')
@click_option('--server_threads', type=click.INT,
              envvar='OPSY_SERVER_THREADS',
              help='Amount of threads.')
@click_option('--server_ssl_enabled', type=click.BOOL, is_flag=True,
              envvar='OPSY_SERVER_SSL_ENABLED',
              help='Set to enable SSL.')
@click_option('--server_certificate', type=click.Path(),
              envvar='OPSY_SERVER_CERTIFICATE',
              help='SSL cert.')
@click_option('--server_private_key', type=click.Path(),
              envvar='OPSY_SERVER_PRIVATE_KEY',
              help='SSL key.')
@click_option('--server_ca_certificate', type=click.Path(),
              envvar='OPSY_SERVER_CA_CERTIFICATE',
              help='SSL CA cert.')
@click.pass_context
def cli(ctx, config, **kwargs):
    overrides = {
        'app': {},
        'auth': {},
        'logging': {},
        'server': {}
    }
    for key, value in kwargs.items():
        top_key, sub_key = key.split('_', 1)
        if value is not None:
            overrides[top_key][sub_key] = value
    try:
        ctx.obj.data['config'] = load_config(config, overrides)
    except NoConfigFile as error:
        print_error(error, exit_script=False)
        ctx.obj.data['config'] = None


cli.add_command(routes_command)
cli.add_command(db_command)


@cli.command('run')
@pass_script_info
def run(script_info):
    """Run the Opsy server."""
    app = script_info.load_app()
    server = create_server(app)
    try:
        host = app.config.opsy['server']['host']
        port = app.config.opsy['server']['port']
        proto = 'https' if server.ssl_adapter else 'http'
        app.logger.info(f'Starting Opsy server at {proto}://{host}:{port}/...')
        app.logger.info(f'API docs available at {proto}://{host}:{port}/docs/')
        server.start()
    except KeyboardInterrupt:
        app.logger.info('Stopping Opsy server...')
    finally:
        server.stop()


@cli.command('shell')
def shell():
    """Run a shell in the app context."""
    from flask.globals import _app_ctx_stack
    banner = 'Welcome to Opsy!'
    app = _app_ctx_stack.top.app
    shell_ctx = {'create_app': create_app,
                 'db': db,
                 'User': User,
                 'Role': Role,
                 'Permission': Permission,
                 'Zone': Zone,
                 'Host': Host,
                 'Group': Group,
                 'HostGroupMapping': HostGroupMapping}
    shell_ctx.update(app.make_shell_context())
    try:
        from IPython import embed
        embed(user_ns=shell_ctx, banner1=banner)
        return
    except ImportError:
        import code
        code.interact(banner, local=shell_ctx)


@db_command.command('init-db')
@click.confirmation_option(
    prompt='This will delete everything. Do you want to continue?')
@with_appcontext
def init_db():
    """Drop everything in database and rebuild the schema."""
    current_app.logger.info('Creating database...')
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command('permission-list')
@click_option('--resource', type=click.STRING)
@click_option('--method', type=click.STRING)
def permission_list(**kwargs):
    """List all permissions the app is aware of."""
    print(AppPermissionSchema(many=True).dumps(
        get_protected_routes(ignored_methods=["HEAD", "OPTIONS"]), indent=4))


@cli.command('create-admin-user')
@click_option('--password', '-p', hide_input=True, confirmation_prompt=True,
              envvar='OPSY_ADMIN_PASSWORD',
              prompt='Password for the new admin user',
              help='Password for the new admin user.')
@click_option('--force', '-f', type=click.BOOL, is_flag=True,
              help='Recreate admin user and role if they already exist.')
def create_admin_user(password, force):
    """Create the default admin user."""
    admin_user = User.query.filter_by(name='admin').first()
    admin_role = Role.query.filter_by(name='admin').first()
    if admin_user and not force:
        print_notice('Admin user already found, exiting. '
                     'Use "--force" to force recreation.')
        sys.exit(0)
    if admin_role and not force:
        print_notice('Admin role already found, exiting. '
                     'Use "--force" to force recreation.')
        sys.exit(0)
    if admin_user:
        print_notice('Admin user already found, deleting.')
        admin_user.delete()
    if admin_role:
        print_notice('Admin role already found, deleting.')
        admin_role.delete()
    admin_user = User.create(
        'admin', password=password, full_name='Default admin user')
    admin_role = Role.create('admin', description='Default admin role')
    for permission in get_valid_permissions():
        admin_role.add_permission(permission)
    admin_role.add_user(admin_user)
    admin_role.save()
    admin_user = User.query.filter_by(name='admin').first()
    admin_role = Role.query.filter_by(name='admin').first()
    print_notice('Admin user created with the specified password:')
    print(UserSchema().dumps(admin_user, indent=4))
    print_notice('Admin role created:')
    print(RoleSchema().dumps(admin_role, indent=4))


@cli.command('version', with_appcontext=False)
def version():
    """Just show the version and quit."""
    print(opsy.__version__)


def main():

    def create_opsy_app(script_info):
        if not script_info.data['config']:
            print_error('Config file not loaded, unable to start app.')
        return create_app(script_info.data['config'])
    cli(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
        obj=ScriptInfo(create_app=create_opsy_app))
