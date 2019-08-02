from functools import wraps
from flask import current_app, request, abort
from flask_allows import allows, Or, Requirement


def is_logged_in(user):
    """Checks if the user is logged in."""
    if current_app.config.get('LOGIN_DISABLED') or user.is_authenticated:
        return True
    return False


def is_same_user(user):
    """Checks if the user is the same user in the request."""
    user_name = request.view_args.get('user_name')
    return user.name == user_name


def need_permission(permission_name, *requirements, identity=None,
                    on_fail=None, throws=None):
    """Modified version of flask_allows requires decorator to tie into RBAC."""

    def decorator(func):

        permission = HasPermission(permission_name)
        if requirements:
            new_requirements = (Or(permission, requirements))
        else:
            new_requirements = (permission,)

        @wraps(func)
        def allower(*args, **kwargs):
            result = allows.run(
                new_requirements,
                identity=identity,
                on_fail=on_fail,
                throws=throws,
                f_args=args,
                f_kwargs=kwargs,
            )
            # authorization failed
            if result is not None:
                return result
            return func(*args, **kwargs)

        rbac_info = {
            'permission_needed': permission_name,
            'requirements': new_requirements
        }
        allower.__rbac__ = rbac_info
        return allower
    return decorator


class HasPermission(Requirement):
    """Checks if the user has the necessary permission to access resource."""

    def __init__(self, permission):
        self.permission = permission

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
        else:
            abort(401)
        return self.permission in permissions

    def __repr__(self):
        return '<{}(\'{}\')>'.format(self.__class__.__name__, self.permission)
