#!/usr/bin/env python2
import os
from flask.ext.script import Manager, Shell
from hourglass.models.api import Client, Check, Event, Stash, db
from hourglass import create_app
import gevent.monkey
gevent.monkey.patch_all()

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def make_shell_context():
    return dict(create_app=create_app, db=db, Check=Check, Client=Client,
                Event=Event, Stash=Stash)

if __name__ == '__main__':
    MANAGER = Manager(create_app)
    MANAGER.add_option('-c', '--config', dest='config', required=False,
                       default='%s/hourglass.ini' % BASEDIR)
    MANAGER.add_command("shell", Shell(make_context=make_shell_context))
    MANAGER.run()
