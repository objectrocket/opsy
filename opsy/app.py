import logging
from logging.handlers import WatchedFileHandler
from logging import StreamHandler
import os.path
import sys
from flask import Flask
from flask_iniconfig import INIConfig
from flask_jsglue import JSGlue
from apscheduler.schedulers.blocking import BlockingScheduler
from opsy.main import core_main
from opsy.db import db
from opsy.exceptions import NoConfigFile, NoConfigSection
from opsy.utils import OpsyJSONEncoder, load_plugins


def create_app(config):
    if not os.path.exists(config):
        raise NoConfigFile('Config %s does not exist' % config)
    app = Flask(__name__)
    JSGlue(app)
    app.jobs = []
    app.config_file = config
    INIConfig(app)
    app.config.from_inifile(config)
    create_logging(app)
    db.init_app(app)
    app.plugin_links = []
    for plugin in load_plugins(app):
        plugin.register_blueprints(app)
        links = plugin.register_link_structure(app)
        app.plugin_links.append(links)

    @app.context_processor
    def inject_links():  # pylint: disable=unused-variable
        return dict(link_structures=app.plugin_links)

    app.register_blueprint(core_main)
    app.json_encoder = OpsyJSONEncoder
    return app


def create_logging(app):
    if not app.debug:
        if not app.config.get('opsy'):
            raise NoConfigSection('Config section "opsy" does not exist')
        opsy_config = app.config.get('opsy')
        log_file = opsy_config.get('log_file')
        formatter = logging.Formatter(
            "%(asctime)s %(process)d %(levelname)s %(module)s - %(message)s")
        log_handlers = [StreamHandler(sys.stdout)]
        if log_file:
            log_handlers.append(WatchedFileHandler(log_file))
        for log_handler in log_handlers:
            log_handler.setFormatter(formatter)
            app.logger.addHandler(log_handler)
        app.logger.setLevel(logging.INFO)


def create_scheduler(app, scheduler_class=BlockingScheduler):
    opsy_config = app.config.get('opsy')
    grace_time = int(opsy_config.get('scheduler_grace_time', 10))
    job_defaults = {
        'misfire_grace_time': grace_time
    }
    scheduler = scheduler_class(job_defaults=job_defaults)
    for plugin in load_plugins(app):
        plugin.register_scheduler_jobs(app)
    for args, kwargs in app.jobs:
        scheduler.add_job(*args, **kwargs)
    return scheduler
