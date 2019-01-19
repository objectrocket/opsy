from datetime import datetime, timezone
from time import time
from flask import current_app
from flask_ldap3_login import AuthenticationResponseStatus
from flask_login import login_user, logout_user
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from opsy.models import User, Role
from opsy.flask_extensions import ldap_manager


def login(username, password, remember=False, force=False, fresh=True):
    if current_app.config.opsy['enable_ldap']:
        result = ldap_manager.authenticate(username, password)
        if not result.status == AuthenticationResponseStatus.success:
            return False
        full_name_attr = current_app.config.opsy['ldap_user_full_name_attr']
        email_attr = current_app.config.opsy['ldap_user_email_attr']
        group_name_attr = current_app.config.opsy['ldap_group_name_attr']
        email = result.user_info[email_attr]
        full_name = result.user_info[full_name_attr]
        user = User.query.filter_by(name=result.user_id).first()
        if not user:
            user = User.create(username, email=email, full_name=full_name)
        else:
            user.update(email=email, full_name=full_name)
        groups = [x[group_name_attr] for x in result.user_groups]
        for role in user.roles:
            if role.ldap_group:
                user.roles.remove(role)
        for role in Role.query.filter(Role.ldap_group.in_(groups)).all():
            user.roles.append(role)
    else:
        user = User.query.filter_by(name=username).first()
        if not user:
            return False
        if not user.verify_password(password):
            return False
    if not login_user(user, remember=remember, force=force, fresh=fresh):
        return False
    return user


def logout(user):
    user.session_token = None
    user.session_token_expires_at = None
    user.save()
    logout_user()


def create_token(user, force_renew=False):
    if not force_renew and verify_token(user):
        return
    ttl = current_app.config.opsy['session_token_ttl']
    seri = Serializer(
        current_app.config['SECRET_KEY'], expires_in=ttl)
    user.session_token = seri.dumps({'id': user.id}).decode('ascii')
    _, header = seri.loads(user.session_token, return_header=True)
    user.session_token_expires_at = datetime.utcfromtimestamp(
        header.get('exp'))
    user.save()


def verify_token(user):  # pylint: disable=R0911
    if user is None:
        return None
    ttl = current_app.config.opsy['session_token_ttl']
    seri = Serializer(current_app.config['SECRET_KEY'])
    try:
        data, header = seri.loads(user.session_token, return_header=True)
    except TypeError:
        return None  # we don't currently have a token
    except SignatureExpired:
        return None  # valid token, but expired
    except BadSignature:
        return None  # invalid token
    if int(user.session_token_expires_at.replace(
            tzinfo=timezone.utc).timestamp()) > time() + ttl:
        return None  # ttl in config has been reduced
    # These next two shouldn't ever happen
    if data.get('id') != user.id:
        return None  # user id doesn't match token payload
    if user.session_token_expires_at != datetime.utcfromtimestamp(
            header.get('exp')):
        return None  # expire times don't match
    return user
