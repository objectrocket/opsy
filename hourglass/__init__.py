from flask import Flask
from flask.ext.iniconfig import INIConfig
from hourglass.backends import db
from hourglass.scheduler import UwsgiScheduler


def create_app(config):
    global app
    app = Flask(__name__)
    INIConfig(app)
    app.config.from_inifile(config)
    parse_config(app)
    db.init_app(app)
    app.scheduler = UwsgiScheduler(app)
    register_blueprints(app)
    return app


def parse_config(app):
    hourglass_config = app.config.get('hourglass')
    app.config['sources'] = {}
    app.config['dashboards'] = {}
    if hourglass_config.get('enabled_sources'):
        enabled_sources = hourglass_config.get('enabled_sources').split(',')
        for source in enabled_sources:
            app.config['sources'][source] = app.config.get(source)
    if hourglass_config.get('enabled_dashboards'):
        enabled_dashboards = hourglass_config.get(
            'enabled_dashboards').split(',')
        for dashboard in enabled_dashboards:
            app.config['dashboards'][dashboard] = app.config.get(dashboard)


def register_blueprints(app):
    from hourglass.views.main import main as main_blueprint
    from hourglass.views.api import api as api_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint, url_prefix='/api')
