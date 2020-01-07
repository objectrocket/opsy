from datetime import datetime, timezone
from time import time
from flask import current_app, g
from flask.sessions import SecureCookieSessionInterface
from flask_ldap3_login import AuthenticationResponseStatus
from flask_login import login_user, logout_user
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from opsy.flask_extensions import ldap_manager


class APISessionInterface(SecureCookieSessionInterface):
    """Prevent creating session from API requests."""

    def save_session(self, *args, **kwargs):
        if g.get('login_via_header'):
            return
        super(APISessionInterface, self).save_session(*args, **kwargs)


def login(user_name, password, force_renew=False):
    # First we try local login
    user = local_login(user_name, password)
    # If that failed we try ldap
    if not user:
        user = ldap_login(user_name, password)
    # If that failed we bail out
    if not user:
        current_app.logger.info(
            f'All login methods failed for user {user_name}.')
        return False
    if not login_user(user):
        current_app.logger.info(f'Login for user {user_name} failed. Disabled?')
        return False
    current_app.logger.info(f'User {user_name} logged in successfully.')
    # Force renewal of the token if it was requested.
    return create_token(user, force_renew=force_renew)


def local_login(user_name, password):
    from opsy.auth.models import User
    current_app.logger.info(f'Attempting local login for user {user_name}...')
    user = User.query.filter_by(name=user_name).first()
    if not user:
        current_app.logger.info(
            f'User {user_name} does not exist, skipping local login.')
        return False
    if user.ldap_user:
        current_app.logger.info(
            f'User {user_name} is an LDAP user, skipping local login.')
        return False
    if not user.verify_password(password):
        current_app.logger.info(f'Incorrect password for user {user_name}.')
        return False
    return user


def ldap_login(user_name, password):  # pylint: disable=too-many-branches
    from opsy.auth.models import User, Role
    current_app.logger.info(f'Attempting LDAP login for user {user_name}...')
    if not current_app.config.opsy['auth']['ldap_enabled']:
        current_app.logger.info(
            f'LDAP login disabled, unable to login user {user_name}.')
        return False
    user = User.query.filter_by(name=user_name).first()
    if user and not user.ldap_user:
        current_app.logger.info(
            f'User {user_name} is a local user, skipping LDAP login.')
        return False
    result = ldap_manager.authenticate(user_name, password)
    if not result.status == AuthenticationResponseStatus.success:
        current_app.logger.info(
            f'LDAP login failed for user {user_name}. Incorrect password?')
        return False
    full_name_attr = \
        current_app.config.opsy['auth']['ldap_user_full_name_attr']
    email_attr = current_app.config.opsy['auth']['ldap_user_email_attr']
    group_name_attr = \
        current_app.config.opsy['auth']['ldap_group_name_attr']
    if isinstance(result.user_info[email_attr], list):
        email = result.user_info[email_attr][0]
    else:
        email = result.user_info[email_attr]
    full_name = result.user_info[full_name_attr]
    user = User.query.filter_by(name=result.user_id).first()
    if not user:
        user = User.create(
            user_name, email=email, full_name=full_name, ldap_user=True)
    else:
        user.update(email=email, full_name=full_name)
    groups = []
    for group in result.user_groups:
        if isinstance(group[group_name_attr], list):
            groups.append(group[group_name_attr][0])
        else:
            groups.append(group[group_name_attr])
    for role in user.roles:
        if role.ldap_group:
            user.roles.remove(role)
    for role in Role.query.filter(Role.ldap_group.in_(groups)).all():
        user.roles.append(role)
    return user.save()


def logout(user):
    if not user:
        return
    username = user.name
    user.session_token = None
    user.session_token_expires_at = None
    for role in user.roles:
        if role.ldap_group:
            user.roles.remove(role)
    user.save()
    logout_user()
    current_app.logger.info(f'{username} logged out successfully.')


def create_token(user, force_renew=False):
    if not force_renew and verify_token(user) is not None:
        return user
    ttl = current_app.config.opsy['auth']['session_token_ttl']
    seri = Serializer(
        current_app.config['SECRET_KEY'], expires_in=ttl)
    user.session_token = seri.dumps({'id': user.id}).decode('ascii')
    _, header = seri.loads(user.session_token, return_header=True)
    user.session_token_expires_at = datetime.fromtimestamp(
        header.get('exp'), tz=timezone.utc)
    return user.save()


def verify_token(user):  # pylint: disable=R0911
    if user is None:
        return None
    ttl = current_app.config.opsy['auth']['session_token_ttl']
    seri = Serializer(current_app.config['SECRET_KEY'])
    try:
        data, header = seri.loads(user.session_token, return_header=True)
    except TypeError:
        return None  # we don't currently have a token
    except SignatureExpired:
        current_app.logger.info(f'Expired token for user {user.name}.')
        return None  # valid token, but expired
    except BadSignature:
        current_app.logger.info(f'Invalid token for user {user.name}.')
        return None  # invalid token
    if int(user.session_token_expires_at.replace(
            tzinfo=timezone.utc).timestamp()) > time() + ttl:
        current_app.logger.info(f'Invalid token ttl for user {user.name}.')
        return None  # ttl in config has been reduced
    # These next two shouldn't ever happen
    if data.get('id') != user.id:
        current_app.logger.info(f'Invalid token id for user {user.name}.')
        return None  # user id doesn't match token payload
    if user.session_token_expires_at != datetime.fromtimestamp(
            header.get('exp'), tz=timezone.utc):
        current_app.logger.info(f'Invalid token exp for user {user.name}.')
        return None  # expire times don't match
    return user


def load_user(session_token):
    from opsy.auth.models import User
    user = User.get_by_token(session_token)
    return verify_token(user)


def load_user_from_request(request):
    from opsy.auth.models import User
    session_token = request.headers.get('X-AUTH-TOKEN')
    user = verify_token(User.get_by_token(session_token))
    g.login_via_header = True
    return user
