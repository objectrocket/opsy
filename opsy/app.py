from flask import Flask
from opsy.config import configure_app
from opsy.flask_extensions import configure_extensions, apispec
from opsy.logging import (configure_logging, log_before_request,
                          log_after_request)
from opsy.auth.views import create_auth_views
from opsy.inventory.views import create_inventory_views


def create_app(config):
    configure_logging(config)
    app = Flask('opsy')
    app.before_request(log_before_request)
    app.after_request(log_after_request)
    configure_app(app, config)
    configure_extensions(app)
    create_views(app)
    return app


def create_views(app):
    create_auth_views(app)
    create_inventory_views(app)
    # Workaround for https://github.com/jmcarp/flask-apispec/issues/111
    # pylint: disable=protected-access
    for key, value in apispec.spec._paths.items():
        apispec.spec._paths[key] = {
            inner_key: inner_value
            for inner_key, inner_value in value.items()
            if inner_key != 'options'
        }
