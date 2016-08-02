from flask import Blueprint


main = Blueprint('main', __name__, template_folder='templates',  # pylint: disable=invalid-name
                 static_url_path='/static/main',
                 static_folder='static')

from . import views  # pylint: disable=wrong-import-position
