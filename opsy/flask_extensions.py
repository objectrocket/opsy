from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_allows import Allows
from flask_apispec.extension import FlaskApiSpec
from flask_jsglue import JSGlue
from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager, current_user
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from prometheus_flask_exporter import PrometheusMetrics

allows = Allows()  # pylint: disable=invalid-name
db = SQLAlchemy()  # pylint: disable=invalid-name
migrate = Migrate()  # pylint: disable=invalid-name
jsglue = JSGlue()  # pylint: disable=invalid-name
ldap_manager = LDAP3LoginManager()  # pylint: disable=invalid-name
login_manager = LoginManager()  # pylint: disable=invalid-name
ma = Marshmallow()  # pylint: disable=invalid-name
apispec = FlaskApiSpec()  # pylint: disable=invalid-name
metrics = PrometheusMetrics(app=None)  # pylint: disable=invalid-name


# pylint: disable=unused-import
def configure_extensions(app):
    # Make SQLAlchemy aware of models
    from opsy.auth import models as am  # noqa: F401
    from opsy.inventory import models as im  # noqa: F401
    from opsy import __version__ as opsy_version  # noqa: F401
    db.init_app(app)
    migrate.init_app(app, db=db)
    ma.init_app(app)
    jsglue.init_app(app)
    login_manager.init_app(app)
    if app.config.opsy['auth']['ldap_enabled']:
        ldap_manager.init_app(app)
    allows.init_app(app)
    allows.identity_loader(lambda: current_user)
    app.config.update({
        'APISPEC_SPEC': APISpec(
            title='opsy',
            version='v1',
            openapi_version='2.0',
            info={'description': "It's Opsy!"},
            plugins=[MarshmallowPlugin()],
            basePath=app.config.opsy['app']['uri_prefix']
        ),
        'APISPEC_SWAGGER_URL': '/docs/swagger.json',
        'APISPEC_SWAGGER_UI_URL': '/docs/',
    })
    app.config['APISPEC_SPEC'].components.security_scheme(
        'api_key', {'type': 'apiKey', 'in': 'header', 'name': 'X-AUTH-TOKEN'})
    apispec.init_app(app)
    from opsy.auth.utils import (load_user, load_user_from_request,
                                 APISessionInterface)
    login_manager.user_loader(load_user)
    login_manager.request_loader(load_user_from_request)
    app.session_interface = APISessionInterface()
    metrics.init_app(app)
    metrics.info('app_info', 'Application info', version=opsy_version)


def finalize_extensions(app):
    # Workaround for https://github.com/jmcarp/flask-apispec/issues/111
    # pylint: disable=protected-access
    for key, value in apispec.spec._paths.items():
        apispec.spec._paths[key] = {
            inner_key: inner_value
            for inner_key, inner_value in value.items()
            if inner_key != 'options'
        }
