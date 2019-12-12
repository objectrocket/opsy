from flask import abort, Blueprint
from flask_allows import requires
from flask_apispec import marshal_with, doc
from flask_login import current_user
from opsy.auth.schema import (
    UserTokenSchema, UserTokenUpdateSchema, UserLoginSchema,
    UserSchema, UserCreateSchema, UserUpdateSchema, UserQuerySchema,
    RoleSchema, RoleUpdateSchema, RoleQuerySchema,
    RolePermissionSchema, RolePermissionUpdateSchema, RolePermissionQuerySchema)
from opsy.auth.models import User, Role, Permission
from opsy.auth.utils import login, logout, create_token
from opsy.flask_extensions import apispec
from opsy.schema import use_kwargs, EmptySchema
from opsy.rbac import is_logged_in, need_permission
from opsy.exceptions import DuplicateError


def create_auth_views(app):
    app.register_blueprint(login_blueprint, url_prefix='/api/v1/login')
    app.register_blueprint(users_blueprint, url_prefix='/api/v1/users')
    app.register_blueprint(roles_blueprint, url_prefix='/api/v1/roles')
    apispec.spec.tag(
        {'name': 'login',
         'description': 'Endpoints for logging in and out of Opsy.'})
    for view in [login_get, login_post, login_patch, login_delete]:
        apispec.register(view, blueprint='auth_login')
    apispec.spec.tag(
        {'name': 'users',
         'description': 'Endpoints for user management.'})
    for view in [users_list, users_post, users_get, users_patch, users_delete]:
        apispec.register(view, blueprint='auth_users')
    apispec.spec.tag(
        {'name': 'roles',
         'description': 'Endpoints for role management.'})
    for view in [roles_list, roles_post, roles_get, roles_patch, roles_delete,
                 role_permissions_list, role_permissions_post,
                 role_permissions_get, role_permissions_patch,
                 role_permissions_delete]:
        apispec.register(view, blueprint='auth_roles')

###############################################################################
# Blueprints
###############################################################################


# pylint: disable=invalid-name
login_blueprint = Blueprint('auth_login', __name__)
# pylint: disable=invalid-name
users_blueprint = Blueprint('auth_users', __name__)
# pylint: disable=invalid-name
roles_blueprint = Blueprint('auth_roles', __name__)

###############################################################################
# Login Views
###############################################################################


@login_blueprint.route('/', methods=['GET'])
@marshal_with(UserTokenSchema(), code=200)
@doc(
    operationId='show_login',
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
    operationId='create_login',
    summary='Login.',
    description='',
    tags=['login'])
def login_post(**kwargs):
    user = login(**kwargs)
    if not user:
        abort(401, 'Username or password incorrect.')
    return current_user


@login_blueprint.route('/', methods=['PATCH'])
@use_kwargs(UserTokenUpdateSchema)
@marshal_with(UserTokenSchema(), code=200)
@doc(
    operationId='patch_login',
    summary='User self-service, such as updating email or password.',
    description='',
    tags=['login'],
    security=[{'api_key': []}])
@requires(is_logged_in)
def login_patch(**kwargs):
    if current_user.ldap_user:
        abort(400, 'This is not available for LDAP users.')
    return current_user.update(**kwargs)


@login_blueprint.route('/', methods=['DELETE'])
@marshal_with(EmptySchema, code=205)
@doc(
    operationId='delete_login',
    summary='Logout.',
    description='',
    tags=['login'],
    security=[{'api_key': []}])
@requires(is_logged_in)
def login_delete():
    logout(current_user)
    return '', 205

###############################################################################
# User Views
###############################################################################


@users_blueprint.route('/', methods=['GET'])
@use_kwargs(UserQuerySchema, locations=['query'])
@marshal_with(UserSchema(many=True), code=200)
@doc(
    operationId='list_users',
    summary='List users.',
    description='',
    tags=['users'],
    security=[{'api_key': []}])
@need_permission('list_users')
def users_list(**kwargs):
    return User.query.filter_in(**kwargs).all()


@users_blueprint.route('/', methods=['POST'])
@use_kwargs(UserCreateSchema)
@marshal_with(UserSchema(), code=201)
@doc(
    operationId='create_user',
    summary='Create a new user.',
    description='',
    tags=['users'],
    security=[{'api_key': []}])
@need_permission('create_user')
def users_post(**kwargs):
    try:
        return User.create(**kwargs), 201
    except (DuplicateError, ValueError) as error:
        abort(400, str(error))


@users_blueprint.route('/<id_or_name>', methods=['GET'])
@marshal_with(UserSchema(), code=200)
@doc(
    operationId='show_user',
    summary='Show a user.',
    description='',
    tags=['users'],
    security=[{'api_key': []}])
@need_permission('show_user')
def users_get(id_or_name):
    try:
        return User.get_by_id_or_name(id_or_name)
    except ValueError as error:
        abort(404, str(error))


@users_blueprint.route('/<id_or_name>', methods=['PATCH'])
@use_kwargs(UserUpdateSchema)
@marshal_with(UserSchema(), code=200)
@doc(
    operationId='update_user',
    summary='Update a user.',
    description='',
    tags=['users'],
    security=[{'api_key': []}])
@need_permission('update_user')
def users_patch(id_or_name, **kwargs):
    try:
        return User.update_by_id_or_name(id_or_name, **kwargs)
    except ValueError as error:
        abort(404, str(error))


@users_blueprint.route('/<id_or_name>', methods=['DELETE'])
@marshal_with(EmptySchema, code=204)
@doc(
    operationId='delete_user',
    summary='Delete a user.',
    description='',
    tags=['users'],
    security=[{'api_key': []}])
@need_permission('delete_user')
def users_delete(id_or_name):
    try:
        User.delete_by_id_or_name(id_or_name)
        return ('', 204)
    except ValueError as error:
        abort(404, str(error))

###############################################################################
# Role Views
###############################################################################


@roles_blueprint.route('/', methods=['GET'])
@use_kwargs(RoleQuerySchema, locations=['query'])
@marshal_with(RoleSchema(many=True), code=200)
@doc(
    operationId='list_roles',
    summary='List roles.',
    description='',
    tags=['roles'],
    security=[{'api_key': []}])
@need_permission('list_roles')
def roles_list(**kwargs):
    return Role.query.filter_in(**kwargs).all()


@roles_blueprint.route('/', methods=['POST'])
@use_kwargs(RoleSchema)
@marshal_with(RoleSchema(), code=201)
@doc(
    operationId='create_role',
    summary='Create a new role.',
    description='',
    tags=['roles'],
    security=[{'api_key': []}])
@need_permission('create_role')
def roles_post(**kwargs):
    try:
        return Role.create(**kwargs), 201
    except (DuplicateError, ValueError) as error:
        abort(400, str(error))


@roles_blueprint.route('/<id_or_name>', methods=['GET'])
@marshal_with(RoleSchema(), code=200)
@doc(
    operationId='show_role',
    summary='Show a role.',
    description='',
    tags=['roles'],
    security=[{'api_key': []}])
@need_permission('show_role')
def roles_get(id_or_name):
    try:
        return Role.get_by_id_or_name(id_or_name)
    except ValueError as error:
        abort(404, str(error))


@roles_blueprint.route('/<id_or_name>', methods=['PATCH'])
@use_kwargs(RoleUpdateSchema)
@marshal_with(RoleSchema(), code=200)
@doc(
    operationId='update_role',
    summary='Update a role.',
    description='',
    tags=['roles'],
    security=[{'api_key': []}])
@need_permission('update_role')
def roles_patch(id_or_name, **kwargs):
    try:
        return Role.update_by_id_or_name(id_or_name, **kwargs)
    except ValueError as error:
        abort(404, str(error))


@roles_blueprint.route('/<id_or_name>', methods=['DELETE'])
@marshal_with(EmptySchema, code=204)
@doc(
    operationId='delete_role',
    summary='Delete a role.',
    description='',
    tags=['roles'],
    security=[{'api_key': []}])
@need_permission('delete_role')
def roles_delete(id_or_name):
    try:
        Role.delete_by_id_or_name(id_or_name)
        return ('', 204)
    except ValueError as error:
        abort(404, str(error))


###############################################################################
# Role Permission Views
###############################################################################


@roles_blueprint.route('/<id_or_name>/permissions/', methods=['GET'])
@use_kwargs(RolePermissionQuerySchema, locations=['query'])
@marshal_with(RolePermissionSchema(many=True), code=200)
@doc(
    operationId='list_role_permissions',
    summary='List role permissions.',
    description='',
    tags=['roles'],
    security=[{'api_key': []}])
@need_permission('show_role')
def role_permissions_list(id_or_name, **kwargs):
    try:
        role = Role.get_by_id_or_name(id_or_name)
    except ValueError as error:
        abort(404, str(error))
    return Permission.query.filter_by(
        role_id=role.id).filter_in(**kwargs).all()


@roles_blueprint.route('/<id_or_name>/permissions/', methods=['POST'])
@use_kwargs(RolePermissionSchema)
@marshal_with(RolePermissionSchema(), code=201)
@doc(
    operationId='create_role_permission',
    summary='Create a role permission.',
    description='',
    tags=['roles'],
    security=[{'api_key': []}])
@need_permission('update_role')
def role_permissions_post(id_or_name, **kwargs):
    try:
        role = Role.get_by_id_or_name(id_or_name)
        permission_name = kwargs['name']
    except ValueError as error:
        abort(404, str(error))
    try:
        return role.add_permission(permission_name), 201
    except (DuplicateError, ValueError) as error:
        abort(400, str(error))


@roles_blueprint.route(
    '/<id_or_name>/permissions/<permission_id_or_name>', methods=['GET'])
@marshal_with(RolePermissionSchema(), code=200)
@doc(
    operationId='show_role_permission',
    summary='Show a role permission.',
    description='',
    tags=['roles'],
    security=[{'api_key': []}])
@need_permission('show_role')
def role_permissions_get(id_or_name, permission_id_or_name):
    try:
        role = Role.get_by_id_or_name(id_or_name)
    except ValueError as error:
        abort(404, str(error))
    try:
        return Permission.get_by_role_and_id_or_name(
            role, permission_id_or_name)
    except ValueError as error:
        abort(404, str(error))


@roles_blueprint.route(
    '/<id_or_name>/permissions/<permission_id_or_name>', methods=['PATCH'])
@use_kwargs(RolePermissionUpdateSchema)
@marshal_with(RolePermissionSchema(), code=200)
@doc(
    operationId='update_role_permission',
    summary='Update a role permission.',
    description='',
    tags=['roles'],
    security=[{'api_key': []}])
@need_permission('update_role')
def role_permissions_patch(id_or_name, permission_id_or_name, **kwargs):
    try:
        role = Role.get_by_id_or_name(id_or_name)
    except ValueError as error:
        abort(404, str(error))
    try:
        return Permission.update_by_role_and_id_or_name(
            role, permission_id_or_name, **kwargs)
    except ValueError as error:
        abort(404, str(error))


@roles_blueprint.route(
    '/<id_or_name>/permissions/<permission_id_or_name>', methods=['DELETE'])
@marshal_with(EmptySchema, code=204)
@doc(
    operationId='delete_role_permission',
    summary='Delete a role permission.',
    description='',
    tags=['roles'],
    security=[{'api_key': []}])
@need_permission('update_role')
def role_permissions_delete(id_or_name, permission_id_or_name):
    try:
        role = Role.get_by_id_or_name(id_or_name)
    except ValueError as error:
        abort(404, str(error))
    try:
        Permission.delete_by_role_and_id_or_name(role, permission_id_or_name)
        return ('', 204)
    except ValueError as error:
        abort(404, str(error))
