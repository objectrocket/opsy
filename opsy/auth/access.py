from collections import namedtuple
from functools import partial
from flask_principal import Permission, UserNeed, ActionNeed


OpsyNeed = namedtuple('OpsyNeed', ['method', 'doc'])  # pylint: disable=invalid-name


needs = {  # pylint: disable=invalid-name
    # General
    'god_mode': OpsyNeed('god_mode', 'Provides all access to everything.'),
    # Users
    'users_create': OpsyNeed('users_create',
                             'Ability to create users in the API.'),
    'users_read': OpsyNeed('view_users',
                           'Ability to list/show users in the API.'),
    'users_update': OpsyNeed('users_update',
                             'Ability to update users in the API.'),
    'users_delete': OpsyNeed('users_delete',
                             'Ability to delete users in the API.'),
    # Roles
    'roles_create': OpsyNeed('roles_create',
                             'Ability to create roles in the API.'),
    'roles_read': OpsyNeed('view_roles',
                           'Ability to list/show roles in the API.'),
    'roles_update': OpsyNeed('roles_update',
                             'Ability to update roles in the API.'),
    'roles_delete': OpsyNeed('roles_delete',
                             'Ability to delete roles in the API.')
}

OpsyPermission = partial(Permission, needs.get('god_mode'),)  # pylint: disable=invalid-name
OpsyPermission.__doc__ = 'Preloads the god_mode need.'


def user_read(user_id):
    return OpsyPermission(needs.get('users_read'), UserNeed(user_id))


def user_update(user_id):
    return OpsyPermission(needs.get('users_update'), UserNeed(user_id))


permissions = {  # pylint: disable=invalid-name
    # General
    'logged_in': OpsyPermission(ActionNeed('logged_in')),
    # Users
    'users_create': OpsyPermission(needs.get('users_create')),
    'users_read': OpsyPermission(needs.get('users_read')),
    'users_update': OpsyPermission(needs.get('users_update')),
    'users_delete': OpsyPermission(needs.get('users_delete')),
    # Single user operations so that users can self-service
    'user_read': user_read,
    'user_update': user_update,
    # Roles
    'roles_create': OpsyPermission(needs.get('roles_create')),
    'roles_read': OpsyPermission(needs.get('roles_read')),
    'roles_update': OpsyPermission(needs.get('roles_update')),
    'roles_delete': OpsyPermission(needs.get('roles_delete'))
}
