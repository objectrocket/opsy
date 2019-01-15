from flask import current_app
from flask_iniconfig import INIConfig
from flask_jsglue import JSGlue
from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager, current_user
from flask_marshmallow import Marshmallow
from flask_principal import Principal, Identity, identity_loaded, UserNeed, \
    ActionNeed, AnonymousIdentity
from flask_sqlalchemy import SQLAlchemy

iniconfig = INIConfig()  # pylint: disable=invalid-name
db = SQLAlchemy()  # pylint: disable=invalid-name
jsglue = JSGlue()  # pylint: disable=invalid-name
login_manager = LoginManager()  # pylint: disable=invalid-name
ldap_manager = LDAP3LoginManager()  # pylint: disable=invalid-name
marshmallow = Marshmallow()  # pylint: disable=invalid-name
principal = Principal()  # pylint: disable=invalid-name


def configure_extensions(app):
    db.init_app(app)
    jsglue.init_app(app)
    marshmallow.init_app(app)
    login_manager.init_app(app)
    if app.config.opsy['enable_ldap']:
        ldap_manager.init_app(app)
    principal.init_app(app)

    @login_manager.user_loader
    def load_user(session_token):  # pylint: disable=unused-variable
        from opsy.models import User
        return User.get_by_token(current_app, session_token)

    @login_manager.request_loader
    def load_user_from_request(request):  # pylint: disable=unused-variable
        session_token = request.headers.get('x-auth-token')
        from opsy.models import User
        return User.get_by_token(current_app, session_token)

    @principal.identity_loader
    def read_identity_from_flask_login():  # pylint: disable=unused-variable
        if current_user.is_authenticated and current_user.is_active:
            return Identity(current_user.id)
        return AnonymousIdentity()

    @identity_loaded.connect_via(app)  # pylint: disable=no-member
    def on_identity_loaded(sender, identity):  # pylint: disable=unused-variable,R0912
        identity.user = current_user
        all_needs = {}
        for catalog in app.needs_catalog.values():
            if catalog is None:
                continue
            for name, need in catalog.items():
                all_needs[name] = need
        if app.config.opsy['base_permissions']:
            for permission_name in app.config.opsy['base_permissions']:
                if all_needs.get(permission_name):
                    identity.provides.add(all_needs.get(permission_name))
        if current_user.is_authenticated and current_user.is_active:
            if hasattr(current_user, 'id'):
                identity.provides.add(UserNeed(current_user.id))
            identity.provides.add(ActionNeed('logged_in'))
            if app.config.opsy['logged_in_permissions']:
                for permission_name in app.config.opsy['logged_in_permissions']:
                    if all_needs.get(permission_name):
                        identity.provides.add(all_needs.get(permission_name))
            if hasattr(current_user, 'permissions'):
                permissions = list(set([x.name for x in  # Dedup
                                        current_user.permissions]))
                for permission in permissions:
                    if all_needs.get(permission):
                        identity.provides.add(all_needs.get(permission))
