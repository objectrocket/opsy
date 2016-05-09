from flask import Flask
from flask.ext.iniconfig import INIConfig


def create_app(config):
    app = Flask(__name__)
    INIConfig(app)
    app.config.from_inifile(config)
    parse_config(app)
    register_blueprints(app)
    print app.config
    return app


def parse_config(app):
    hourglass_config = app.config.get('hourglass')
    enabled_regions = hourglass_config.get('enabled_sensu_nodes').split(',')
    app.config['sensu_nodes'] = {}
    for region in enabled_regions:
        app.config['sensu_nodes'][region] = app.config.get(region)


def register_blueprints(app):
    from views.main import main as main_blueprint
    from views.api import api as api_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint, url_prefix='/api')
