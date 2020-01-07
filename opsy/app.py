from flask import Flask
from opsy.config import configure_app
from opsy.flask_extensions import configure_extensions, finalize_extensions
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
    finalize_extensions(app)
    return app


def create_views(app):
    create_auth_views(app)
    create_inventory_views(app)
