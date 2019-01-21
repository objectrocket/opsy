from collections import namedtuple
from functools import partial
from flask import current_app, request
from flask_allows import Requirement


Need = namedtuple(  # pylint: disable=invalid-name
    'Need', ['plugin', 'name', 'doc'])
CoreNeed = partial(Need, 'core')  # pylint: disable=invalid-name

god_mode = CoreNeed(  # pylint: disable=invalid-name
    'god_mode', 'Provides all access to everything.')
# Users
users_create = CoreNeed(  # pylint: disable=invalid-name
    'users_create', 'Ability to create users in the API.')
users_read = CoreNeed(  # pylint: disable=invalid-name
    'users_read', 'Ability to list/show users in the API.')
users_update = CoreNeed(  # pylint: disable=invalid-name
    'users_update', 'Ability to update users in the API.')
users_delete = CoreNeed(  # pylint: disable=invalid-name
    'users_delete', 'Ability to delete users in the API.')
# Roles
roles_create = CoreNeed(  # pylint: disable=invalid-name
    'roles_create', 'Ability to create roles in the API.')
roles_read = CoreNeed(  # pylint: disable=invalid-name
    'roles_read', 'Ability to list/show roles in the API.')
roles_update = CoreNeed(  # pylint: disable=invalid-name
    'roles_update', 'Ability to update roles in the API.')
roles_delete = CoreNeed(  # pylint: disable=invalid-name
    'roles_delete', 'Ability to delete roles in the API.')

core_needs = [  # pylint: disable=invalid-name
    god_mode, users_create, users_read, users_update, users_delete,
    roles_create, roles_read, roles_update, roles_delete
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
        return self.permission in permissions or god_mode.name in permissions


def is_logged_in(user):
    if current_app.config.get('LOGIN_DISABLED') or user.is_authenticated:
        return True
    return False


def is_same_user(user):
    """Checks if the user is the same user in the request."""
    user_name = request.view_args.get('user_name')
    return user.name == user_name
