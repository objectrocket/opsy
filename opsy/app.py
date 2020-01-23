from flask import Flask
from opsy.config import configure_app
from opsy.flask_extensions import configure_extensions, finalize_extensions
from opsy.logging import (configure_logging, log_before_request,
                          log_after_request)
from opsy.auth.views import create_auth_views
from opsy.inventory.views import create_inventory_views


class PrefixMiddleware:

    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        start_response('404', [('Content-Type', 'text/plain')])
        return ["This url does not belong to the app.".encode()]


def create_app(config):
    configure_logging(config)
    app = Flask('opsy')
    app.wsgi_app = PrefixMiddleware(
        app.wsgi_app, prefix=config['app']['uri_prefix'])
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
