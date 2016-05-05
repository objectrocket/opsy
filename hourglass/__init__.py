from flask import Flask
from flask.ext.iniconfig import INIConfig
#from hourglass.cache import cache


def create_app(config):
    app = Flask(__name__)
    #cache.init_app(app)
    INIConfig(app)
    app.config.from_inifile(config)
    hourglass_config = app.config.get('hourglass')
    enabled_regions = hourglass_config.get('enabled_regions').split(',')
    app.config['regions'] = {}
    for region in enabled_regions:
        app.config['regions'][region] = app.config.get(region)
    register_blueprints(app)
    return app


def register_blueprints(app):
    from views.main import main as main_blueprint
    from views.api import api as api_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint, url_prefix='/api')
