import logging
from logging.handlers import WatchedFileHandler
from flask import Flask
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from opsy.flask_extensions import configure_extensions, apispec
from opsy.utils import OpsyJSONEncoder, load_plugins
from opsy.config import load_config
from opsy.auth.views import create_auth_views
from opsy.inventory.views import create_inventory_views


def create_app(config_file):
    app = Flask(__name__)
    load_config(app, config_file)
    create_logging(app)
    configure_extensions(app)
    create_views(app)
    app.jobs = []  # FIXME: Need to handle scheduled jobs better.
    app.json_encoder = OpsyJSONEncoder
    return app


def create_logging(app):
    if not app.debug:
        log_handlers = []
        log_file = app.config.opsy['log_file']
        if log_file:
            log_handlers.append(WatchedFileHandler(log_file))
        formatter = logging.Formatter(
            "%(asctime)s %(process)d %(levelname)s %(module)s - %(message)s")
        for log_handler in log_handlers:
            app.logger.addHandler(log_handler)
        for log_handler in app.logger.handlers:
            log_handler.setFormatter(formatter)
        app.logger.setLevel(logging.INFO)


def create_views(app):
    create_auth_views(app)
    create_inventory_views(app)
    # Workaround for https://github.com/jmcarp/flask-apispec/issues/111
    # pylint: disable=protected-access
    for key, value in apispec.spec._paths.items():
        apispec.spec._paths[key] = {
            inner_key: inner_value
            for inner_key, inner_value in value.items()
            if inner_key != 'options'
        }


def create_scheduler(app, scheduler_class=AsyncIOScheduler):
    job_defaults = {
        'misfire_grace_time': app.config.opsy['scheduler_grace_time']
    }
    scheduler = scheduler_class(job_defaults=job_defaults)
    for plugin in load_plugins(app):
        plugin.register_scheduler_jobs(app)
    for args, kwargs in app.jobs:
        scheduler.add_job(*args, **kwargs)
    return scheduler
