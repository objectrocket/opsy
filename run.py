#!/usr/bin/env python2

from hourglass import create_app
from flask.ext.script import Manager, Shell
import os

basedir = os.path.abspath(os.path.dirname(__file__))


def make_shell_context():
    return dict()

if __name__ == '__main__':
    manager = Manager(create_app)
    manager.add_option('-c', '--config', dest='config', required=False,
                       default='%s/config.ini' % basedir)
    manager.add_command("shell", Shell(make_context=make_shell_context))
    manager.run()
