import os
from flask_script import Manager
import hourglass
from hourglass.backends.cache import (Check, Client, Event, Silence, Result,
                                      Zone)
from hourglass.scheduler import Scheduler
from hourglass.db import db
from hourglass.app import create_app

DEFAULT_CONFIG = '%s/hourglass.ini' % os.path.abspath(os.path.curdir)
MANAGER = Manager(create_app)
MANAGER.add_option('-V', '--version', action='version',
                   version=hourglass.__version__)
MANAGER.add_option('-c', '--config', dest='config', default=DEFAULT_CONFIG)


@MANAGER.shell
def make_shell_context():
    return dict(create_app=create_app, db=db, Check=Check, Client=Client,
                Event=Event, Silence=Silence, Result=Result, Zone=Zone,
                Scheduler=Scheduler, MANAGER=MANAGER)


@MANAGER.command
def initcache():
    """Drop everything in cache database and rebuilds schema."""
    Scheduler(MANAGER.app.config_file).create_cache_db()
    print("Done!")


@MANAGER.command
def updatecache():
    """Update the cache database."""
    Scheduler(MANAGER.app.config_file).run_tasks()
    print("Done!")


def main():
    MANAGER.run()
