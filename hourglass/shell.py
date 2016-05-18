import os
from flask.ext.script import Manager, Shell
from hourglass.models.backends.sensu.cache import Client, Check, Event, Stash, db
from . import create_app

BASEDIR = os.path.abspath(os.path.curdir)


def make_shell_context():
    return dict(create_app=create_app, db=db, Check=Check, Client=Client,
                Event=Event, Stash=Stash)


def run_hourglass(cwd=BASEDIR):
    manager = Manager(create_app)
    manager.add_option('-c', '--config', dest='config', required=False,
                       default='%s/hourglass.ini' % cwd)
    manager.add_command('shell', Shell(make_context=make_shell_context))
    manager.run()
