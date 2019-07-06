from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_allows import Allows
from flask_apispec.extension import FlaskApiSpec
from flask_iniconfig import INIConfig
from flask_jsglue import JSGlue
from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager, current_user
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from opsy.resources import ResourceManager

allows = Allows()  # pylint: disable=invalid-name
db = SQLAlchemy()  # pylint: disable=invalid-name
iniconfig = INIConfig()  # pylint: disable=invalid-name
jsglue = JSGlue()  # pylint: disable=invalid-name
ldap_manager = LDAP3LoginManager()  # pylint: disable=invalid-name
login_manager = LoginManager()  # pylint: disable=invalid-name
ma = Marshmallow()  # pylint: disable=invalid-name
rm = ResourceManager(route_prefix='/api/v1/')  # pylint: disable=invalid-name
docs = FlaskApiSpec()  # pylint: disable=invalid-name


def configure_extensions(app):
    # Make SQLAlchemy aware of models
    from opsy.auth import models as am  # noqa: F401
    from opsy.inventory import models as im  # noqa: F401
    from opsy.monitoring import models as mm  # noqa: F401
    db.init_app(app)
    ma.init_app(app)
    jsglue.init_app(app)
    login_manager.init_app(app)
    if app.config.opsy['enable_ldap']:
        ldap_manager.init_app(app)
    allows.init_app(app)
    allows.identity_loader(lambda: current_user)
    app.config.update({
        'APISPEC_SPEC': APISpec(
            title='opsy',
            version='v1',
            openapi_version="3.0.2",
            plugins=[MarshmallowPlugin()],
        ),
        'APISPEC_SWAGGER_URL': '/swagger/',
    })
    docs.init_app(app)
    rm.init_app(app, docs=docs)
    from opsy.auth.resources import RolesAPI
    from opsy.inventory.resources import (
        ZonesAPI, HostsAPI, GroupsAPI, HostGroupMappingsAPI)
    rm.add_resource(RolesAPI)
    rm.add_resource(ZonesAPI)
    rm.add_resource(HostsAPI)
    rm.add_resource(GroupsAPI)
    rm.add_resource(HostGroupMappingsAPI)

    @login_manager.user_loader
    def load_user(session_token):  # pylint: disable=unused-variable
        from opsy.auth.models import User
        from opsy.auth import verify_token
        user = User.get_by_token(session_token)
        return verify_token(user)

    @login_manager.request_loader
    def load_user_from_request(request):  # pylint: disable=unused-variable
        session_token = request.headers.get('x-auth-token')
        from opsy.auth.models import User
        from opsy.auth import verify_token
        user = User.get_by_token(session_token)
        return verify_token(user)
