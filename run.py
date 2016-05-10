#!/usr/bin/env python2
import os
from hourglass import create_app
from flask.ext.script import Manager, Shell
import gevent.monkey
gevent.monkey.patch_all()

basedir = os.path.abspath(os.path.dirname(__file__))


def make_shell_context():
    return dict()

if __name__ == '__main__':
    manager = Manager(create_app)
    manager.add_option('-c', '--config', dest='config', required=False,
                       default='%s/hourglass.ini' % basedir)
    manager.add_command("shell", Shell(make_context=make_shell_context))
    manager.run()
