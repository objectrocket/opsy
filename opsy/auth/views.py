from flask import abort, Blueprint, current_app
from flask_allows import requires, Or
from flask_apispec import marshal_with, doc
from flask_login import current_user
from opsy.flask_extensions import apispec
from opsy.schema import use_kwargs
from opsy.auth.utils import login, logout, create_token
from opsy.auth.schema import (UserSchema, UserLoginSchema,
                              UserTokenSchema, UserSettingSchema, RoleSchema)
from opsy.auth.models import User, Role
from opsy.exceptions import DuplicateError
from opsy.rbac import is_logged_in


def create_auth_views(app):
    app.register_blueprint(login_blueprint, url_prefix='/api/v1/login')
    apispec.spec.tag(
        {'name': 'login',
         'description': 'Endpoints for logging in and out of Opsy.'})
    for view in [login_get, login_post, login_delete]:
        apispec.register(view, blueprint='auth_login')

###############################################################################
# Blueprints
###############################################################################


login_blueprint = Blueprint('auth_login', __name__)

###############################################################################
# Login Views
###############################################################################


@login_blueprint.route('/', methods=['GET'])
@marshal_with(UserTokenSchema(), code=200)
@doc(
    summary='Get auth token.',
    description='',
    tags=['login'],
    security=[{'api_key': []}])
@requires(is_logged_in)
def login_get():
    create_token(current_user)
    return current_user


@login_blueprint.route('/', methods=['POST'])
@use_kwargs(UserLoginSchema)
@marshal_with(UserTokenSchema(), code=200)
@doc(
    summary='Login.',
    description='',
    tags=['login'])
def login_post(**kwargs):
    user = login(kwargs['user_name'], kwargs['password'],
                 remember=kwargs.get('remember_me'))
    if not user:
        abort(401, 'Username or password incorrect.')
    return current_user


@login_blueprint.route('/', methods=['DELETE'])
@marshal_with(None, code=205)
@doc(
    summary='Logout.',
    description='',
    tags=['login'],
    security=[{'api_key': []}])
@requires(is_logged_in)
def login_delete():
    logout(current_user)
    return '', 205
