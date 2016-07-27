from flask import Flask
from flask.ext.iniconfig import INIConfig
from hourglass.db import db
from hourglass.backends.sensu.cache import *
from hourglass.exceptions import NoConfigFile
from hourglass.utils import HourglassJSONEncoder
import logging
from logging.handlers import WatchedFileHandler
from logging import StreamHandler
import os.path
import sys


def create_app(config):
    if not os.path.exists(config):
        raise NoConfigFile('Config %s does not exist' % config)
    app = Flask(__name__)
    app.config_file = config
    INIConfig(app)
    app.config.from_inifile(config)
    setup_logging(app)
    parse_config(app)
    db.init_app(app)
    register_blueprints(app)
    app.json_encoder = HourglassJSONEncoder
    return app


def setup_logging(app):
    if not app.debug:
        config = app.config
        hourglass_config = config.get('hourglass')
        log_file = hourglass_config.get('log_file')
        formatter = logging.Formatter(
            "%(asctime)s %(process)d %(levelname)s %(module)s - %(message)s")
        if log_file:
            log_handler = WatchedFileHandler(log_file)
            log_handler.setFormatter(formatter)
            app.logger.addHandler(log_handler)
        log_handler = StreamHandler(sys.stdout)
        log_handler.setFormatter(formatter)
        app.logger.addHandler(log_handler)
        app.logger.setLevel(logging.INFO)


def parse_config(app):
    hourglass_config = app.config.get('hourglass')
    app.config['zones'] = {}
    app.config['dashboards'] = {}
    if hourglass_config.get('enabled_zones'):
        enabled_zones = hourglass_config.get('enabled_zones').split(',')
        for zone in enabled_zones:
            app.config['zones'][zone] = app.config[zone]
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
                continue  # TODO: raise and exception here


def register_blueprints(app):
    from hourglass.views.main import main as main_blueprint
    from hourglass.views.api import api as api_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint, url_prefix='/api')
