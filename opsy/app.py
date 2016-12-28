import logging
from logging.handlers import WatchedFileHandler
from logging import StreamHandler
import sys
from flask import Flask
from apscheduler.schedulers.blocking import BlockingScheduler
from opsy.main import core_main
from opsy.api import core_api
from opsy.extensions import configure_extensions
from opsy.utils import OpsyJSONEncoder, load_plugins
from opsy.config import load_config, validate_config
from opsy.auth.access import needs


def create_app(config_file):
    app = Flask(__name__)
    load_config(app, config_file)
    create_logging(app)
    configure_extensions(app)
    app.jobs = []  # FIXME: Need to handle scheduled jobs better.
    app.needs_catalog = {'core': needs}
    app.register_blueprint(core_main)
    app.register_blueprint(core_api)
    for plugin in load_plugins(app):
        validate_config(app, plugin=plugin)
        app.needs_catalog[plugin.name] = plugin.needs
        plugin.register_blueprints(app)
    app.json_encoder = OpsyJSONEncoder
    app.plugin_links = [{
        'name': 'About',
        'id': 'about',
        'content': 'core_main.about',
        'get_vars': None,
        'type': 'link'
    }]

    @app.before_first_request
    def load_plugin_links():  # pylint: disable=unused-variable
        for plugin in load_plugins(app):
            plugin.register_link_structure(app)

    @app.context_processor
    def inject_links():  # pylint: disable=unused-variable
        return dict(link_structures=app.plugin_links)
    return app


def create_logging(app):
    if not app.debug:
        log_handlers = [StreamHandler(sys.stdout)]
        log_file = app.config.opsy['log_file']
        if log_file:
            log_handlers.append(WatchedFileHandler(log_file))
        formatter = logging.Formatter(
            "%(asctime)s %(process)d %(levelname)s %(module)s - %(message)s")
        for log_handler in log_handlers:
            log_handler.setFormatter(formatter)
            app.logger.addHandler(log_handler)
        app.logger.setLevel(logging.INFO)


def create_scheduler(app, scheduler_class=BlockingScheduler):
    job_defaults = {
        'misfire_grace_time': app.config.opsy['scheduler_grace_time']
    }
    scheduler = scheduler_class(job_defaults=job_defaults)
    for plugin in load_plugins(app):
        plugin.register_scheduler_jobs(app)
    for args, kwargs in app.jobs:
        scheduler.add_job(*args, **kwargs)
    return scheduler
