import os
from flask.ext.script import Command, Manager, Shell
from hourglass.models.backends.sensu.cache import Client, Check, Event, Result, Stash, db
from hourglass.models.poller import Poller
from . import create_app

BASEDIR = os.path.abspath(os.path.curdir)


def make_shell_context():
    return dict(create_app=create_app, db=db, Poller=Poller, Check=Check,
                Client=Client, Event=Event, Stash=Stash, Result=Result)


class init_db(Command):
    "Initializes the database with default values (DATA DESTRUCTIVE!)"

    def run(self):
        db.drop_all()
        db.create_all()
        print("Done!")


def run_hourglass(cwd=BASEDIR):
    manager = Manager(create_app)
    manager.add_option('-c', '--config', dest='config', required=False,
                       default='%s/hourglass.ini' % cwd)
    manager.add_command('shell', Shell(make_context=make_shell_context))
    manager.add_command("initdb", init_db())
    manager.run()
