from flask import Blueprint
from os.path import abspath, join, dirname

datapath = abspath(dirname(__file__))

main = Blueprint('main', __name__, template_folder=join(datapath, 'templates'),
                 static_url_path='/static/main',
                 static_folder=join(datapath, 'static'))  # pylint: disable=invalid-name

from . import views  # pylint: disable=wrong-import-position
