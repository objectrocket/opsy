import os
from flask_script import Manager
import opsy
# from opsy.backends.cache import (Check, Client, Event, Silence, Result,
#                                  Zone)
from opsy.db import db
from opsy.app import create_app, create_scheduler
from opsy.utils import load_plugins
from stevedore import extension

DEFAULT_CONFIG = '%s/opsy.ini' % os.path.abspath(os.path.curdir)
MANAGER = Manager(create_app)
MANAGER.add_option('-V', '--version', action='version',
                   version=opsy.__version__)
MANAGER.add_option('-c', '--config', dest='config', default=DEFAULT_CONFIG)


@MANAGER.command
def runscheduler():
    """Run the scheduler."""
    scheduler = create_scheduler(MANAGER.app)
    try:
        MANAGER.app.logger.info('Starting the scheduler')
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        MANAGER.app.logger.info('Stopping the scheduler')


@MANAGER.shell
def make_shell_context():
    shell_vars = {'create_app': create_app, 'db': db}
    for plugin in load_plugins(MANAGER.app):
        plugin.register_shell_objects(shell_vars)
    return shell_vars


@MANAGER.command
def initcache():
    """Drop everything in cache database and rebuilds schema."""
    MANAGER.app.logger.info('Creating cache database')
    db.drop_all(bind='cache')
    db.create_all(bind='cache')
    db.session.commit()
    print("Done!")


# @MANAGER.command
# def updatecache():
#     """Update the cache database."""
#     Scheduler(MANAGER.app.config_file).run_tasks()
#     print("Done!")


def main():
    mgr = extension.ExtensionManager(namespace='opsy.plugin',
                                     invoke_on_load=False)
    for ext in mgr:
        for command, func in ext.plugin.get_cli_commands():
            MANAGER.add_command(command, func)
    MANAGER.run()
