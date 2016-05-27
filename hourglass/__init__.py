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
    app.config['zones'] = {}
    app.config['dashboards'] = {}
    if hourglass_config.get('enabled_zones'):
        enabled_zones = hourglass_config.get('enabled_zones').split(',')
        for zone in enabled_zones:
            required_keys = ['backend', 'host', 'port']
            if any(app.config[zone].get(key) is None for key in required_keys):
                pass  # TODO: raise an exception here
            app.config['zones'][zone] = {}
            app.config['zones'][zone]['backend'] = app.config[zone].get('backend')
            app.config['zones'][zone]['host'] = app.config[zone].get('host')
            app.config['zones'][zone]['port'] = app.config[zone].get('port')
            app.config['zones'][zone]['timeout'] = int(app.config[zone].get('timeout', 10))
    if hourglass_config.get('enabled_dashboards'):
        enabled_dashboards = hourglass_config.get(
            'enabled_dashboards').split(',')
        for dashboard in enabled_dashboards:
            if app.config.get(dashboard):
                app.config['dashboards'][dashboard] = {}
                dash_config = app.config['dashboards'][dashboard]
                dash_config['zone'] = app.config[dashboard].get('zone')
                dash_config['check'] = app.config[dashboard].get('check')
                dash_config['check'] = app.config[dashboard].get('check')
            else:
                pass  # TODO: raise and exception here


def register_blueprints(app):
    from hourglass.views.main import main as main_blueprint
    from hourglass.views.api import api as api_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint, url_prefix='/api')
