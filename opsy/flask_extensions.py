from flask import current_app
from flask_allows import Allows
from flask_iniconfig import INIConfig
from flask_jsglue import JSGlue
from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager, current_user
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

allows = Allows()  # pylint: disable=invalid-name
db = SQLAlchemy()  # pylint: disable=invalid-name
iniconfig = INIConfig()  # pylint: disable=invalid-name
jsglue = JSGlue()  # pylint: disable=invalid-name
ldap_manager = LDAP3LoginManager()  # pylint: disable=invalid-name
login_manager = LoginManager()  # pylint: disable=invalid-name
ma = Marshmallow()  # pylint: disable=invalid-name


def configure_extensions(app):
    db.init_app(app)
    ma.init_app(app)
    jsglue.init_app(app)
    login_manager.init_app(app)
    if app.config.opsy['enable_ldap']:
        ldap_manager.init_app(app)
    allows.init_app(app)
    allows.identity_loader(lambda: current_user)

    @login_manager.user_loader
    def load_user(session_token):  # pylint: disable=unused-variable
        from opsy.models import User
        from opsy.auth import verify_token
        user = User.get_by_token(session_token)
        return verify_token(user)

    @login_manager.request_loader
    def load_user_from_request(request):  # pylint: disable=unused-variable
        session_token = request.headers.get('x-auth-token')
        from opsy.models import User
        from opsy.auth import verify_token
        user = User.get_by_token(session_token)
        return verify_token(user)
