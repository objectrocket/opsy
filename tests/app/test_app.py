import logging
import os
import pytest
import requests
from flask import Flask
from marshmallow import ValidationError
from opsy.config import load_config
from opsy.exceptions import NoConfigFile

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def test_app_created(app):
    """Make sure create_app isn't short changing us."""
    assert isinstance(app, Flask)


def test_swagger_json(client):
    """Make sure we have our swagger spec available."""
    response = client.get('/docs/swagger.json')
    assert response.status_code == 200
    assert b"It's Opsy!" in response.data


def test_swagger_ui(client):
    """Make sure the swagger UI is also there."""
    response = client.get('/docs/')
    assert response.status_code == 200
    assert b"Swagger UI" in response.data


def test_config(app):
    """Make sure we load in config and whatnot."""
    # Make sure it yells at us if the config file isn't found
    with pytest.raises(NoConfigFile):
        load_config(
            f'{CURRENT_DIR}/../data/not_real_opsy_config.toml')
    # Make sure it yells if the DB connection string isn't provided.
    with pytest.raises(ValidationError, match=r'.*database_uri.*'):
        load_config(
            f'{CURRENT_DIR}/../data/fake_opsy_config_no_db.toml')
    # Make sure it yells if no secret key is provided.
    with pytest.raises(ValidationError, match=r'.*secret_key.*'):
        load_config(
            f'{CURRENT_DIR}/../data/fake_opsy_config_no_secret_key.toml')
    # Make sure it yells if we don't have an app section.
    with pytest.raises(ValidationError, match=r'.*app.*'):
        load_config(
            f'{CURRENT_DIR}/../data/fake_opsy_config_no_section.toml')
    # Make sure it yells if we don't have and ldap_host with ldap_enabled.
    with pytest.raises(ValidationError, match=r'.*ldap_host.*'):
        load_config(
            f'{CURRENT_DIR}/../data/fake_opsy_config_no_ldap_host.toml')
    # Make sure it yells at us if we enable ssl but don't give cert or key.
    with pytest.raises(ValidationError, match=r'.*ssl_enabled.*'):
        load_config(
            f'{CURRENT_DIR}/../data/fake_opsy_config_no_ssl.toml')
    # Make sure our flask config makes it to the app.
    config = load_config(f'{CURRENT_DIR}/../test_opsy_config.toml')
    assert app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] is False
    assert app.config['SECRET_KEY'] == config['app']['secret_key']
    assert app.config['SQLALCHEMY_DATABASE_URI'] == \
        config['app']['database_uri']


def test_logging(app, caplog):
    """Make sure logging is working."""
    app_logger = logging.getLogger('opsy')
    app_logger.info('this is a test message')
    assert 'test message' in caplog.text
    with open('/tmp/opsy.log', 'r') as opsy_log_file:
        assert 'test message' in opsy_log_file.readlines()[-1]
    access_logger = logging.getLogger('opsy_access')
    access_logger.info('this is a test access message')
    assert 'test access message' in caplog.text
    with open('/tmp/opsy_access.log', 'r') as opsy_access_log_file:
        assert 'test access message' in opsy_access_log_file.readlines()[-1]


def test_server(test_server):
    """Test the wsgi server."""
    config = load_config(f'{CURRENT_DIR}/../test_opsy_config.toml')
    host = config['server']['host']
    port = config['server']['port']
    response = requests.get(f'http://{host}:{port}/docs/swagger.json')
    assert response.status_code == 200
    assert "It's Opsy!" in response.text
