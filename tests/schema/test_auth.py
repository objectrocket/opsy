import datetime as dt
import pytest
from collections import OrderedDict
from opsy.auth.schema import (
    UserLoginSchema, PermissionSchema, UserTokenSchema, UserSchema,
    RoleSchema, RolePermissionSchema)
from opsy.auth.utils import create_token
from opsy.auth.models import Permission
from marshmallow.exceptions import ValidationError


###############################################################################
# UserLoginSchema Tests
###############################################################################


def test_user_login_schema():

    def make_payload(u='user', p='pass', r=False):
        """Return schema payload with all arguments."""
        return {'user_name': u, 'password': p, 'remember_me': r}

    payload = make_payload()
    expected_user_login_schema_input = payload
    test_user = payload
    assert UserLoginSchema().load(test_user) == expected_user_login_schema_input

    nouser = make_payload(u=None)
    with pytest.raises(ValidationError):
        UserLoginSchema().load(nouser)

    nopass = make_payload(p=None)
    with pytest.raises(ValidationError):
        UserLoginSchema().load(nopass)


###############################################################################
# PermissionSchema Tests
###############################################################################


def test_permission_schema():

    expected_permission_schema_input = {
        'endpoint': 'test',
        'method': 'test',
        'permission_needed': 'test'}
    expected_permission_schema_output = OrderedDict([
        ('endpoint', 'test'),
        ('method', 'test'),
        ('permission_needed', 'test')])

    assert PermissionSchema().dump(expected_permission_schema_input) \
        == expected_permission_schema_output


###############################################################################
# UserSchema Tests
###############################################################################


def test_user_schema(test_user):

    expected_user_schema_output = OrderedDict([
        ('id', test_user.id),
        ('name', test_user.name),
        ('full_name', 'Test User'),
        ('email', None),
        ('enabled', True),
        ('created_at', test_user.created_at.replace(
            tzinfo=dt.timezone.utc).isoformat()),
        ('updated_at', test_user.updated_at.replace(
            tzinfo=dt.timezone.utc).isoformat()),
        ('roles', []),
        ('permissions', [])])

    assert UserSchema().dump(test_user) == expected_user_schema_output


###############################################################################
# UserTokenSchema Tests
###############################################################################


def test_user_token_schema(test_user):

    create_token(test_user)

    expected_zone_schema_output = OrderedDict([
        ('user_id', test_user.id),
        ('user_name', test_user.name),
        ('token', test_user.session_token),
        ('expires_at', test_user.session_token_expires_at.replace(
            tzinfo=dt.timezone.utc).isoformat())])

    assert UserTokenSchema().dump(test_user) == expected_zone_schema_output


###############################################################################
# RoleSchema Tests
###############################################################################


def test_role_schema(test_role):

    expected_role_schema_output = OrderedDict([
        ('id', test_role.id),
        ('name', test_role.name),
        ('ldap_group', test_role.ldap_group),
        ('description', test_role.description),
        ('created_at', test_role.created_at.replace(
            tzinfo=dt.timezone.utc).isoformat()),
        ('updated_at', test_role.updated_at.replace(
            tzinfo=dt.timezone.utc).isoformat()),
        ('permissions', test_role.permissions),
        ('users', test_role.users)])

    assert RoleSchema().dump(test_role) == expected_role_schema_output


###############################################################################
# RolePermissionSchema Tests
###############################################################################


def test_role_permission_schema(admin_user):

    test_perm = Permission.query.first()

    expected_role_permission_schema_output = OrderedDict([
        ('id', test_perm.id),
        ('role', OrderedDict([
            ('id', test_perm.role.id),
            ('name', test_perm.role.name)])),
        ('name', test_perm.name),
        ('created_at', test_perm.created_at.replace(
            tzinfo=dt.timezone.utc).isoformat()),
        ('updated_at', test_perm.updated_at.replace(
            tzinfo=dt.timezone.utc).isoformat())])

    assert RolePermissionSchema().dump(test_perm) \
        == expected_role_permission_schema_output
