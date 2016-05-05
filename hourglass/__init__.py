from flask import Flask
import json

HGCONFIG = {}


def create_app(config, mode):
    app = Flask(__name__)
    get_config()
    register_blueprints(app)
    return app


def get_config(path='./hourglass.json'):
    global HGCONFIG
    if len(HGCONFIG) > 0:
        return HGCONFIG
    with open('./hourglass.json') as conffile:
        HGCONFIG = json.load(conffile)
    return HGCONFIG


def register_blueprints(app):
    from views.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
