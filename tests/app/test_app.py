import os
import pytest
from flask import Flask
from opsy.app import create_app
from opsy.config import load_config
from opsy.exceptions import NoConfigFile, NoConfigSection, MissingConfigOption

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


def test_config():
    """Make sure we load in config and whatnot."""
    # Make sure it yells at us if the config file isn't found
    with pytest.raises(NoConfigFile):
        create_app(f'{CURRENT_DIR}/../data/not_real_opsy_config.ini')
