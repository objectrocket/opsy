import pytest
from collections import OrderedDict
from opsy.auth.schema import (
    UserLoginSchema, AppPermissionSchema, UserTokenSchema, UserSchema,
    RoleSchema, RolePermissionSchema)
from opsy.auth.utils import create_token
from opsy.auth.models import Permission
from marshmallow.exceptions import ValidationError


###############################################################################
# UserLoginSchema Tests
###############################################################################


def test_user_login_schema():

    def make_payload(u='user', p='pass', f=False):
        """Return schema payload with all arguments."""
        return {'user_name': u, 'password': p, 'force_renew': f}

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
# AppPermissionSchema Tests
###############################################################################


def test_app_permission_schema():

    expected_permission_schema_input = {
        'endpoint': 'test',
        'method': 'test',
        'permission_needed': 'test'}
    expected_permission_schema_output = OrderedDict([
        ('endpoint', 'test'),
        ('method', 'test'),
        ('permission_needed', 'test')])

    assert AppPermissionSchema().dump(expected_permission_schema_input) \
        == expected_permission_schema_output


###############################################################################
# UserSchema Tests
###############################################################################


def test_user_schema(test_user):

    expected_user_schema_output = OrderedDict([
        ('id', test_user.id),
        ('name', test_user.name),
        ('full_name', test_user.full_name),
        ('email', test_user.email),
        ('enabled', test_user.enabled),
        ('ldap_user', test_user.ldap_user),
        ('created_at', test_user.created_at.isoformat()),
        ('updated_at', test_user.updated_at.isoformat()),
        ('roles', [
            OrderedDict([
                ('id', x.id),
                ('name', x.name),
                ('_links', {
                    'self': f'/api/v1/roles/{x.id}',
                    'collection': '/api/v1/roles/'})])
            for x in test_user.roles]),
        ('permissions', [OrderedDict([
            ('id', x.id),
            ('name', x.name),
            ('_links', {
                'self': f'/api/v1/roles/{x.role.id}/permissions/{x.id}',
                'collection': f'/api/v1/roles/{x.role.id}/permissions/'})])
            for x in test_user.permissions]),
        ('_links', {
            'self': f'/api/v1/users/{test_user.id}',
            'collection': '/api/v1/users/'})])

    assert UserSchema().dump(test_user) == expected_user_schema_output


###############################################################################
# UserTokenSchema Tests
###############################################################################


def test_user_token_schema(test_user):

    create_token(test_user)

    expected_zone_schema_output = OrderedDict([
        ('user_id', test_user.id),
        ('user_name', test_user.name),
        ('full_name', test_user.full_name),
        ('email', test_user.email),
        ('ldap_user', test_user.ldap_user),
        ('token', test_user.session_token),
        ('expires_at', test_user.session_token_expires_at.isoformat())])

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
        ('created_at', test_role.created_at.isoformat()),
        ('updated_at', test_role.updated_at.isoformat()),
        ('permissions', [OrderedDict([
            ('id', x.id),
            ('name', x.name),
            ('_links', {
                'self': f'/api/v1/roles/{x.role.id}/permissions/{x.id}',
                'collection': f'/api/v1/roles/{x.role.id}/permissions/'})])
            for x in test_role.permissions]),
        ('users', test_role.users),
        ('_links', {
            'self': f'/api/v1/roles/{test_role.id}',
            'collection': '/api/v1/roles/'})])

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
            ('name', test_perm.role.name),
            ('_links', {
                'self': f'/api/v1/roles/{test_perm.role.id}',
                'collection': '/api/v1/roles/'})])),
        ('name', test_perm.name),
        ('created_at', test_perm.created_at.isoformat()),
        ('updated_at', test_perm.updated_at.isoformat()),
        ('_links', {
            'self': f'/api/v1/roles/{test_perm.role.id}/permissions/{test_perm.id}',
            'collection': f'/api/v1/roles/{test_perm.role.id}/permissions/'})])

    assert RolePermissionSchema().dump(test_perm) \
        == expected_role_permission_schema_output
