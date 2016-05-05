from flask import Flask
import json


def create_app(config, mode):
    app = Flask(__name__)
    app.debug = True
    app.config['hourglass_config'] = get_config()
    register_blueprints(app)
    return app


def get_config(path='./hourglass.json'):
    with open('./hourglass.json') as conffile:
        HGCONFIG = json.load(conffile)
    return HGCONFIG


def register_blueprints(app):
    from views.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
