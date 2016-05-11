from flask import Blueprint

api = Blueprint('api', __name__)  # pylint: disable=invalid-name

from . import views  # pylint: disable=wrong-import-position
