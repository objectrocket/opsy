import os
from flask import current_app
from flask.cli import FlaskGroup, run_command
from opsy.db import db
from opsy.app import create_app, create_scheduler
from opsy.utils import load_plugins

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
        current_app.logger.info('Starting the scheduler')
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        current_app.logger.info('Stopping the scheduler')


@cli.command('shell')
def shell():
    """Run a shell in the app context."""
    from flask.globals import _app_ctx_stack
    banner = 'Welcome to Opsy!'
    app = _app_ctx_stack.top.app
    shell_ctx = {'create_app': create_app,
                 'create_scheduler': create_scheduler,
                 'db': db}
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


@cli.command('init-cache')
def init_cache():
    """Drop everything in cache database and rebuild the schema."""
    current_app.logger.info('Creating cache database')
    db.drop_all(bind='cache')
    db.create_all(bind='cache')
    db.session.commit()


def main():
    with create_opsy_app(None).app_context():
        for plugin in load_plugins(current_app):
            plugin.register_cli_commands(cli)
    cli()
