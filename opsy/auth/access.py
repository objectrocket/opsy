from collections import namedtuple
from functools import partial
from flask_principal import Permission, UserNeed, ActionNeed


OpsyNeed = namedtuple('OpsyNeed', ['method', 'doc'])  # pylint: disable=invalid-name


needs = {  # pylint: disable=invalid-name
    # General
    'god_mode': OpsyNeed('god_mode', 'Provides all access to everything.'),
    # Users
    'create_users': OpsyNeed('create_users',
                             'Ability to create users in the API.'),
    'read_users': OpsyNeed('view_users',
                           'Ability to list/show users in the API.'),
    'update_users': OpsyNeed('update_users',
                             'Ability to update users in the API.'),
    'delete_users': OpsyNeed('delete_users',
                             'Ability to delete users in the API.')
}

OpsyPermission = partial(Permission, needs.get('god_mode'),)  # pylint: disable=invalid-name
OpsyPermission.__doc__ = 'Preloads the god_mode need and.'


def delete_user(user_id):
    return OpsyPermission(needs.get('delete_users'), UserNeed(user_id))


def read_user(user_id):
    return OpsyPermission(needs.get('read_users'), UserNeed(user_id))


def update_user(user_id):
    return OpsyPermission(needs.get('update_users'), UserNeed(user_id))


permissions = {  # pylint: disable=invalid-name
    # General
    'logged_in': OpsyPermission(ActionNeed('logged_in')),
    # Users
    'create_users': OpsyPermission(needs.get('create_users')),
    'read_users': OpsyPermission(needs.get('read_users')),
    'update_users': OpsyPermission(needs.get('update_users')),
    'delete_users': OpsyPermission(needs.get('delete_users')),
    # Single user operations so that users can self-service
    'read_user': read_user,
    'update_user': update_user,
    'delete_user': delete_user
}
