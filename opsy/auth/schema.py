from marshmallow import fields as ma_fields
from marshmallow import RAISE
from marshmallow_sqlalchemy import field_for
from opsy.auth.models import User, Role, Permission
from opsy.flask_extensions import ma
from opsy.schema import BaseSchema, Hyperlinks

###############################################################################
# Non-sqlalchemy schemas
###############################################################################


class UserLoginSchema(BaseSchema):

    user_name = ma_fields.String(load_only=True, required=True)
    password = ma_fields.String(load_only=True, required=True)
    force_renew = ma_fields.Boolean(load_only=True, default=False,
                                    missing=False)


class AppPermissionSchema(BaseSchema):
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
        fields = ('id', 'name', 'full_name', 'email', 'enabled', 'ldap_user',
                  'created_at', 'updated_at', 'roles', 'permissions', '_links')
        ordered = True
        unknown = RAISE

    id = field_for(User, 'id', dump_only=True)
    name = field_for(User, 'name', required=True)
    email = field_for(
        User, 'email', field_class=ma.Email)  # pylint: disable=no-member
    created_at = field_for(User, 'created_at', dump_only=True)
    updated_at = field_for(User, 'updated_at', dump_only=True)

    permissions = ma.Nested(  # pylint: disable=no-member
        'RolePermissionRefSchema', many=True, dump_only=True)
    roles = ma.Nested(  # pylint: disable=no-member
        'RoleRefSchema', many=True, dump_only=True)
    _links = Hyperlinks(
        {"self": ma.URLFor("auth_users.users_get", id_or_name="<id>"),
         "collection": ma.URLFor("auth_users.users_list")},
        dump_only=True
    )


class UserCreateSchema(UserSchema):
    """
    UserCreateSchema.

    This exists because the password field with load_only=True was still
    being rendered on the output UserSchema. Seems like a bug, but I didn't
    want to fight it.
    """

    class Meta:
        model = User
        fields = ('name', 'full_name', 'email', 'enabled', 'ldap_user',
                  'password')
        ordered = True
        unknown = RAISE

    password = ma_fields.String(required=True, load_only=True)


class UserUpdateSchema(UserSchema):

    class Meta:
        model = User
        fields = ('name', 'full_name', 'email', 'enabled', 'ldap_user',
                  'password')
        ordered = True
        unknown = RAISE

    name = field_for(User, 'name', required=False)
    password = ma_fields.String(load_only=True)


class UserQuerySchema(UserSchema):

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'permission_name',
                  'role_id', 'role_name', 'enabled', 'ldap_user')
        ordered = True
        unknown = RAISE

    id = field_for(User, 'id')
    name = field_for(User, 'name', required=False)
    email = field_for(User, 'email')
    permission_name = ma_fields.String(attribute='permissions___name')
    role_id = ma_fields.String(attribute='role___id')
    role_name = ma_fields.String(attribute='role___name')
    enabled = field_for(User, 'enabled')


class UserRefSchema(UserSchema):

    class Meta:
        model = User
        fields = ('id', 'name', '_links')
        ordered = True
        unknown = RAISE


class UserTokenSchema(UserSchema):

    class Meta:
        model = User
        fields = ('id', 'name', 'full_name', 'email', 'ldap_user',
                  'session_token', 'session_token_expires_at')
        ordered = True
        unknown = RAISE

    id = field_for(User, 'id', data_key='user_id', dump_only=True)
    name = field_for(User, 'name', data_key='user_name', required=True)
    password = ma_fields.String(required=True, load_only=True)
    session_token = field_for(
        User, 'session_token', data_key='token', dump_only=True)
    session_token_expires_at = field_for(
        User, 'session_token_expires_at', data_key='expires_at',
        dump_only=True)


class UserTokenUpdateSchema(UserSchema):

    class Meta:
        model = User
        fields = ('full_name', 'email', 'password')
        ordered = True
        unknown = RAISE


class RoleSchema(BaseSchema):

    class Meta:
        model = Role
        fields = ('id', 'name', 'ldap_group', 'description', 'created_at',
                  'updated_at', 'permissions', 'users', '_links')
        ordered = True
        unknown = RAISE

    id = field_for(Role, 'id', dump_only=True)
    name = field_for(Role, 'name', required=True)
    created_at = field_for(Role, 'created_at', dump_only=True)
    updated_at = field_for(Role, 'updated_at', dump_only=True)

    permissions = ma.Nested(  # pylint: disable=no-member
        'RolePermissionRefSchema', many=True, dump_only=True)
    users = ma.Nested(  # pylint: disable=no-member
        'UserRefSchema', many=True, dump_only=True)

    _links = Hyperlinks(
        {"self": ma.URLFor("auth_roles.roles_get", id_or_name="<id>"),
         "collection": ma.URLFor("auth_roles.roles_list")},
        dump_only=True)


class RoleUpdateSchema(RoleSchema):

    class Meta:
        model = Role
        fields = ('name', 'ldap_group', 'description')
        ordered = True
        unknown = RAISE

    name = field_for(Role, 'name', required=False)


class RoleQuerySchema(RoleSchema):

    class Meta:
        model = Role
        fields = ('id', 'name', 'ldap_group', 'permssion_name',
                  'user_name', 'user_id')
        ordered = True
        unknown = RAISE

    id = field_for(Role, 'id')
    name = field_for(Role, 'name', required=False)
    ldap_group = field_for(Role, 'ldap_group')
    permission_name = ma_fields.String(attribute='permissions___name')
    user_name = ma_fields.String(attribute='users___name')
    user_id = ma_fields.String(attribute='users___id')


class RoleRefSchema(RoleSchema):

    class Meta:
        model = Role
        fields = ('id', 'name', '_links')
        ordered = True
        unknown = RAISE


class RolePermissionSchema(BaseSchema):

    class Meta:
        model = Permission
        fields = ('id', 'role', 'name', 'created_at', 'updated_at', '_links')
        ordered = True

    id = field_for(Permission, 'id', dump_only=True)
    name = field_for(Permission, 'name', required=True)
    created_at = field_for(Permission, 'created_at', dump_only=True)
    updated_at = field_for(Permission, 'updated_at', dump_only=True)

    role = ma.Nested(  # pylint: disable=no-member
        'RoleRefSchema', dump_only=True)

    _links = Hyperlinks({
        "self": ma.URLFor("auth_roles.role_permissions_get",
                          id_or_name="<role_id>",
                          permission_id_or_name="<id>"),
        "collection": ma.URLFor("auth_roles.role_permissions_list",
                                id_or_name="<role_id>")}, dump_only=True)


class RolePermissionUpdateSchema(BaseSchema):

    class Meta:
        model = Permission
        fields = ('name', )
        ordered = True

    name = field_for(Permission, 'name', required=False)


class RolePermissionQuerySchema(RolePermissionSchema):

    class Meta:
        model = Permission
        fields = ('id', 'name')
        ordered = True
        uknown = RAISE

    id = field_for(Permission, 'id')
    name = field_for(Permission, 'name', required=False)


class RolePermissionRefSchema(RolePermissionSchema):

    class Meta:
        model = Permission
        fields = ('id', 'name', '_links')
        ordered = True
        unknown = RAISE
