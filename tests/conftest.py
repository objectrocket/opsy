import threading
import time
import pytest
from opsy.app import create_app
from opsy.config import load_config
from opsy.server import create_server
from tests.data import auth, inventory
from opsy.flask_extensions import db as opsy_db


###############################################################################
# Flask Fixtures
###############################################################################


@pytest.fixture(scope='session')
def app():
    test_app = create_app(load_config('tests/test_opsy_config.toml'))
    test_app.config['TESTING'] = True
    return test_app


@pytest.fixture(scope='session')
def _db(app):
    opsy_db.app = app
    opsy_db.drop_all()
    opsy_db.create_all()
    opsy_db.session.commit()
    yield opsy_db
    opsy_db.session.remove()
    opsy_db.drop_all()
    opsy_db.session.bind.dispose()


@pytest.fixture(scope='function')
def test_server(app):
    host = app.config.opsy['server']['host']
    port = app.config.opsy['server']['port']
    server = create_server(app, host, port)
    server.shutdown_timeout = 0  # Speed-up tests teardown
    threading.Thread(target=server.safe_start).start()
    while not server.ready:  # wait until fully initialized and bound
        time.sleep(0.1)
    yield server
    server.stop()


###############################################################################
# Auth Fixtures
###############################################################################


@pytest.fixture(scope='function')
def test_user(db_session):
    """Creates a test user."""
    return auth.test_user()


@pytest.fixture(scope='function')
def disabled_user(db_session):
    """Creates a disabled user."""
    return auth.disabled_user()


@pytest.fixture(scope='function')
def admin_user(db_session):
    """Creates a test admin user."""
    return auth.admin_user()


@pytest.fixture(scope='function')
def test_users(db_session):
    """Creates test users."""
    return auth.test_users()


@pytest.fixture(scope='function')
def test_role(db_session):
    """Creates a test role."""
    return auth.test_role()


@pytest.fixture(scope='function')
def test_roles(db_session):
    """Creates test roles."""
    return auth.test_roles()


###############################################################################
# Inventory Fixtures
###############################################################################


@pytest.fixture(scope='function')
def test_zone(db_session):
    """Creates a test zone."""
    return inventory.test_zone()


@pytest.fixture(scope='function')
def test_zones(db_session):
    """Creates test zones."""
    return inventory.test_zones()


@pytest.fixture(scope='function')
def test_group(db_session):
    """Creates a test group."""
    return inventory.test_group()


@pytest.fixture(scope='function')
def test_groups(db_session):
    """Creates test groups."""
    return inventory.test_groups()


@pytest.fixture(scope='function')
def test_host(db_session):
    """Creates a test host."""
    return inventory.test_host()


@pytest.fixture(scope='function')
def test_hosts(db_session):
    """Creates test hosts."""
    return inventory.test_hosts()


@pytest.fixture(scope='function')
def test_inventory_bootstrap(db_session, mocker):
    """Creates a test inventory environment."""

    # This is to workaround the race condition outlined in this issue:
    # https://github.com/jeancochrane/pytest-flask-sqlalchemy/issues/18
    # Seems to only really bite us with the inventory tests, so just putting
    # here.
    mocker.patch.object(db_session, 'remove', lambda: None)
    return inventory.test_inventory_bootstrap()
