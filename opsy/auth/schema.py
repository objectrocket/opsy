from marshmallow import fields as ma_fields
from marshmallow import RAISE
from marshmallow_sqlalchemy import field_for
from opsy.auth.models import User, Role, Permission
from opsy.flask_extensions import ma
from opsy.schema import BaseSchema

###############################################################################
# Non-sqlalchemy schemas
###############################################################################


class UserLoginSchema(BaseSchema):

    user_name = ma_fields.String(load_only=True, required=True)
    password = ma_fields.String(load_only=True, required=True)
    remember_me = ma_fields.Boolean(load_only=True, default=False,
                                    missing=False)
    # force_renew = ma_fields.Boolean(load_only=True, default=False,
    #                                 missing=False)


class PermissionSchema(BaseSchema):
    class Meta:
        fields = ('endpoint', 'method', 'permission_needed')
        ordered = True
        unknown = RAISE

    endpoint = ma_fields.String()
    method = ma_fields.String()
    permission_needed = ma_fields.String()

###############################################################################
# Sqlalchemy schemas
###############################################################################


class UserSchema(BaseSchema):

    class Meta:
        model = User
        fields = ('id', 'name', 'full_name', 'email', 'enabled', 'created_at',
                  'updated_at', 'roles', 'permissions')
        ordered = True
        unknown = RAISE

    id = field_for(User, 'id', dump_only=True)
    name = field_for(User, 'name', required=True)
    email = field_for(
        User, 'email', field_class=ma.Email)  # pylint: disable=no-member
    created_at = field_for(User, 'created_at', dump_only=True)
    updated_at = field_for(User, 'updated_at', dump_only=True)

    permissions = ma_fields.Pluck(
        'RolePermissionSchema', 'name', many=True, dump_only=True)
    roles = ma_fields.Pluck(
        'RoleSchema', 'name', many=True, dump_only=True)


class UserTokenSchema(BaseSchema):

    class Meta:
        model = User
        fields = ('id', 'name', 'session_token', 'session_token_expires_at')
        ordered = True
        unknown = RAISE

    id = field_for(User, 'id', data_key='user_id', dump_only=True)
    name = field_for(User, 'name', data_key='user_name', required=True)
    password = ma_fields.String(required=True, load_only=True)
    remember_me = ma_fields.Boolean(load_only=True)
    force_renew = ma_fields.Boolean(load_only=True)
    session_token = field_for(
        User, 'session_token', data_key='token', dump_only=True)
    session_token_expires_at = field_for(
        User, 'session_token_expires_at', data_key='expires_at',
        dump_only=True)
    submit = ma_fields.String(load_only=True)  # submit button on login


class RoleSchema(BaseSchema):

    class Meta:
        model = Role
        fields = ('id', 'name', 'ldap_group', 'description', 'created_at',
                  'updated_at', 'permissions', 'users')
        ordered = True
        unknown = RAISE

    id = field_for(Role, 'id', dump_only=True)
    name = field_for(Role, 'name', required=True)
    created_at = field_for(Role, 'created_at', dump_only=True)
    updated_at = field_for(Role, 'updated_at', dump_only=True)

    permissions = ma_fields.Pluck(
        'RolePermissionSchema', 'name', many=True, dump_only=True)
    users = ma_fields.Pluck(
        'UserSchema', 'name', many=True, dump_only=True)


class RolePermissionSchema(BaseSchema):

    class Meta:
        model = Permission
        fields = ('id', 'role', 'name', 'created_at', 'updated_at')
        ordered = True

    id = field_for(Permission, 'id', dump_only=True)
    name = field_for(Permission, 'name', required=True)
    created_at = field_for(Permission, 'created_at', dump_only=True)
    updated_at = field_for(Permission, 'updated_at', dump_only=True)

    role = ma.Nested(  # pylint: disable=no-member
        'RoleSchema', dump_only=True, only=['id', 'name'])
