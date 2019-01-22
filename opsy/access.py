from collections import namedtuple
from functools import partial
from flask import current_app, request
from flask_allows import Requirement


Need = namedtuple(  # pylint: disable=invalid-name
    'Need', ['plugin', 'name', 'doc'])
CoreNeed = partial(Need, 'core')  # pylint: disable=invalid-name

GOD_MODE = CoreNeed(
    'god_mode', 'Provides all access to everything.')
# Users
USERS_CREATE = CoreNeed(
    'users_create', 'Ability to create users in the API.')
USERS_READ = CoreNeed(
    'users_read', 'Ability to list/show users in the API.')
USERS_UPDATE = CoreNeed(
    'users_update', 'Ability to update users in the API.')
USERS_DELETE = CoreNeed(
    'users_delete', 'Ability to delete users in the API.')
# Roles
ROLES_CREATE = CoreNeed(
    'roles_create', 'Ability to create roles in the API.')
ROLES_READ = CoreNeed(
    'roles_read', 'Ability to list/show roles in the API.')
ROLES_UPDATE = CoreNeed(
    'roles_update', 'Ability to update roles in the API.')
ROLES_DELETE = CoreNeed(
    'roles_delete', 'Ability to delete roles in the API.')

CORE_NEEDS = [
    GOD_MODE, USERS_CREATE, USERS_READ, USERS_UPDATE, USERS_DELETE,
    ROLES_CREATE, ROLES_READ, ROLES_UPDATE, ROLES_DELETE
]


class HasPermission(Requirement):
    """Checks if the user has the necessary permission to access resource."""

    def __init__(self, permission):
        self.permission = permission.name

    def fulfill(self, user):
        if current_app.config.get('LOGIN_DISABLED'):
            return True
        # Everyone gets base permissions
        permissions = current_app.config.opsy['base_permissions']
        if user.is_authenticated and user.is_active:
            # Logged in users get logged in permissions
            permissions.extend(
                current_app.config.opsy['logged_in_permissions'])
            # And a user gets their own permissions from their roles
            if hasattr(user, 'permissions'):
                permissions.extend([x.name for x in user.permissions])
        return self.permission in permissions or GOD_MODE.name in permissions


def is_logged_in(user):
    if current_app.config.get('LOGIN_DISABLED') or user.is_authenticated:
        return True
    return False


def is_same_user(user):
    """Checks if the user is the same user in the request."""
    user_name = request.view_args.get('user_name')
    return user.name == user_name
