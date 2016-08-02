import logging
from logging.handlers import WatchedFileHandler
from logging import StreamHandler
import os.path
import sys
from flask import Flask
from flask.ext.iniconfig import INIConfig
from opsy.db import db
from opsy.backends.sensu.cache import *
from opsy.exceptions import NoConfigFile
from opsy.utils import OpsyJSONEncoder, load_zones


def create_app(config):
    if not os.path.exists(config):
        raise NoConfigFile('Config %s does not exist' % config)
    app = Flask(__name__)
    app.config_file = config
    INIConfig(app)
    app.config.from_inifile(config)
    setup_logging(app)
    parse_config(app)
    load_zones(app.config)  # make sqlalchemy aware of any plugins
    db.init_app(app)
    register_blueprints(app)
    app.json_encoder = OpsyJSONEncoder
    return app


def setup_logging(app):
    if not app.debug:
        config = app.config
        opsy_config = config.get('opsy')
        log_file = opsy_config.get('log_file')
        formatter = logging.Formatter(
            "%(asctime)s %(process)d %(levelname)s %(module)s - %(message)s")
        if log_file:
            log_handler = WatchedFileHandler(log_file)
        else:
            log_handler = StreamHandler(sys.stdout)  # pylint: disable=redefined-variable-type
        log_handler.setFormatter(formatter)
        app.logger.addHandler(log_handler)
        app.logger.setLevel(logging.INFO)


def parse_config(app):
    opsy_config = app.config.get('opsy')
    app.config['zones'] = {}
    app.config['dashboards'] = {}
    if opsy_config.get('enabled_zones'):
        enabled_zones = opsy_config.get('enabled_zones').split(',')
        for zone in enabled_zones:
            app.config['zones'][zone] = app.config[zone]
    if opsy_config.get('enabled_dashboards'):
        enabled_dashboards = opsy_config.get(
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
    from opsy.views.main import main as main_blueprint
    from opsy.views.api import api as api_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint, url_prefix='/api')
