import logging
from logging.handlers import WatchedFileHandler
from logging import StreamHandler
import sys
from flask import Flask
from flask_jsglue import JSGlue
from apscheduler.schedulers.blocking import BlockingScheduler
from opsy.main import core_main
from opsy.auth.models import User
from opsy.db import db
from opsy.extensions import login_manager
from opsy.utils import OpsyJSONEncoder, load_plugins, load_config
from opsy.config import SCHEDULER_GRACE_TIME, LOG_FILE


def create_app(config_file):
    app = Flask(__name__)
    load_config(app, config_file)
    create_logging(app)
    configure_extensions(app)
    app.register_blueprint(core_main)
    app.json_encoder = OpsyJSONEncoder
    app.plugin_links = [{
        'name': 'About',
        'id': 'about',
        'content': 'core_main.about',
        'get_vars': None,
        'type': 'link'
    }]

    for plugin in load_plugins(app):
        plugin.register_blueprints(app)

    @app.before_first_request
    def load_plugin_links():  # pylint: disable=unused-variable
        for plugin in load_plugins(app):
            plugin.register_link_structure(app)

    @app.context_processor
    def inject_links():  # pylint: disable=unused-variable
        return dict(link_structures=app.plugin_links)
    return app


def configure_extensions(app):
    JSGlue(app)

    # flask_sqlalchemy
    db.init_app(app)

    # flask-login
    # login_manager.login_view = 'frontend.login'
    # login_manager.refresh_view = 'frontend.reauth'
    #
    @login_manager.user_loader
    def load_user(user_id):  # pylint: disable=unused-variable
        return User.get_by_id(user_id)

    login_manager.init_app(app)
    #
    # # flask-principal (must be configed after flask-login!!!)
    # principal.init_app(app)
    #
    # @identity_loaded.connect_via(app)
    # def on_identity_loaded(sender, identity):
    #     pass


def create_logging(app):
    if not app.debug:
        log_handlers = [StreamHandler(sys.stdout)]
        log_file = app.opsy_config.get('log_file', LOG_FILE)
        if log_file:
            log_handlers.append(WatchedFileHandler(log_file))
        formatter = logging.Formatter(
            "%(asctime)s %(process)d %(levelname)s %(module)s - %(message)s")
        for log_handler in log_handlers:
            log_handler.setFormatter(formatter)
            app.logger.addHandler(log_handler)
        app.logger.setLevel(logging.INFO)


def create_scheduler(app, scheduler_class=BlockingScheduler):
    app.jobs = []
    job_defaults = {
        'misfire_grace_time': int(app.opsy_config.get('scheduler_grace_time',
                                                      SCHEDULER_GRACE_TIME))
    }
    scheduler = scheduler_class(job_defaults=job_defaults)
    for plugin in load_plugins(app):
        plugin.register_scheduler_jobs(app)
    for args, kwargs in app.jobs:
        scheduler.add_job(*args, **kwargs)
    return scheduler
