import sys
import time
import logging
from logging.handlers import WatchedFileHandler
from flask import request, g
from flask_login import current_user


def log_before_request():
    """Needed to log on user logout since current_user is wiped."""
    if current_user.is_authenticated:
        g.logged_user = current_user.name
    else:
        g.logged_user = None


def log_after_request(response):
    """Apache style access logs."""
    access_logger = logging.getLogger('opsy_access')
    if current_user.is_authenticated:
        username = current_user.name
    else:
        username = g.logged_user or '-'
    timestamp = time.strftime("%d/%b/%Y:%H:%M:%S %z")
    length = response.headers.get('Content-Length') or '-'
    message = (
        f'{request.remote_addr} - {username} [{timestamp}] "{request.method} '
        f'{request.full_path} {request.environ.get("SERVER_PROTOCOL", "-")}" '
        f'{response.status_code} {length}')
    access_logger.info(message)
    return response


def configure_logging(config):
    # Nuke any default handlers
    logging.getLogger().handlers = []
    # First configure the application logger.
    app_logger = logging.getLogger('opsy')
    app_log_handlers = [logging.StreamHandler(sys.stdout)]
    if config['logging']['log_file']:
        app_log_handlers.append(
            WatchedFileHandler(config['logging']['log_file']))
    for log_handler in app_log_handlers:
        log_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s %(process)d %(levelname)s %(module)s - '
                '%(message)s'))
        app_logger.addHandler(log_handler)
    app_logger.setLevel(config['logging']['log_level'])
    # Now configure the access logger.
    access_logger = logging.getLogger('opsy_access')
    access_log_handlers = [logging.StreamHandler(sys.stdout)]
    if config['logging']['access_log_file']:
        access_log_handlers.append(
            WatchedFileHandler(config['logging']['access_log_file']))
    for log_handler in access_log_handlers:
        log_handler.setFormatter(
            logging.Formatter('%(message)s'))
        access_logger.addHandler(log_handler)
    access_logger.setLevel(config['logging']['log_level'])
