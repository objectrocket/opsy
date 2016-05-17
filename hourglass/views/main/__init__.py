from flask import Blueprint
from os.path import abspath, join, dirname


main = Blueprint('main', __name__, template_folder='templates',
                 static_url_path='/static/main',
                 static_folder='static')  # pylint: disable=invalid-name

from . import views  # pylint: disable=wrong-import-position
