from opsy.flask_extensions import ma
from opsy.models import Permission, Role, User, UserSetting
from marshmallow_sqlalchemy import field_for
from marshmallow import RAISE
from marshmallow import fields as ma_fields


class PermissionSchema(ma.ModelSchema):

    class Meta:
        name = 'permission'
        plural_name = 'permissions'
        model = Permission
        fields = ('id', 'role', 'name', 'created_at', 'updated_at')
        ordered = True

    id = field_for(Permission, 'id', dump_only=True)
    name = field_for(Permission, 'name', required=True)
    created_at = field_for(Permission, 'created_at', dump_only=True)
    updated_at = field_for(Permission, 'updated_at', dump_only=True)

    role = ma.Nested(
        'RoleSchema', dump_only=True, only=['id', 'name'])


class UserSchema(ma.ModelSchema):

    class Meta:
        name = 'user'
        plural_name = 'users'
        model = User
        fields = ('id', 'name', 'full_name', 'email', 'enabled', 'created_at',
                  'updated_at', 'settings', 'roles', 'permissions')
        ordered = True
        unknown = RAISE

    id = field_for(User, 'id', dump_only=True)
    name = field_for(User, 'name', required=True)
    email = field_for(User, 'email', field_class=ma.Email)
    created_at = field_for(User, 'created_at', dump_only=True)
    updated_at = field_for(User, 'updated_at', dump_only=True)

    settings = ma.Nested(
        'UserSettingSchema', many=True, dump_only=True, only=['key', 'value'])
    permissions = ma_fields.Pluck(
        'PermissionSchema', 'name', many=True, dump_only=True)
    roles = ma.Nested(
        'RoleSchema', many=True, dump_only=True, only=['name', 'permissions'])


class UserLoginSchema(ma.Schema):

    user_name = ma_fields.String(load_only=True, required=True)
    password = ma_fields.String(load_only=True, required=True)
    remember_me = ma_fields.Boolean(load_only=True, default=False, missing=False)
    force_renew = ma_fields.Boolean(load_only=True, default=False, missing=False)


class UserTokenSchema(ma.ModelSchema):

    class Meta:
        name = 'auth'
        plural_name = 'auth'
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


class UserSettingSchema(ma.ModelSchema):

    class Meta:
        name = 'user_setting'
        plural_name = 'user_settings'
        model = UserSetting
        fields = ('id', 'user_name', 'key', 'value', 'created_at',
                  'updated_at')
        ordered = True
        unknown = RAISE

    id = field_for(UserSetting, 'id', dump_only=True)
    key = field_for(UserSetting, 'key', required=True)
    value = field_for(UserSetting, 'value', required=True)
    created_at = field_for(User, 'created_at', dump_only=True)
    updated_at = field_for(User, 'updated_at', dump_only=True)

    user_name = ma_fields.Pluck(
        'UserSchema', 'name', dump_only=True)


class RoleSchema(ma.ModelSchema):

    class Meta:
        name = 'role'
        plural_name = 'roles'
        model = Role
        fields = ('id', 'name', 'created_at', 'updated_at', 'ldap_group',
                  'description', 'permissions', 'users')
        ordered = True
        unknown = RAISE

    id = field_for(Role, 'id', dump_only=True)
    name = field_for(Role, 'name', required=True)
    created_at = field_for(Role, 'created_at', dump_only=True)
    updated_at = field_for(Role, 'updated_at', dump_only=True)

    permissions = ma_fields.Pluck(
        'PermissionSchema', 'name', many=True, dump_only=True)
    users = ma_fields.Pluck(
        'UserSchema', 'name', many=True, dump_only=True)
