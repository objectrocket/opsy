from functools import wraps
from flask import current_app, request
from flask_allows import allows, Or


def is_logged_in(user):
    """Checks if the user is logged in."""
    if current_app.config.get('LOGIN_DISABLED') or \
            (user.is_authenticated and user.is_active):
        return True
    return False


def is_same_user(user):
    """Checks if the user is the same user in the request."""
    user_name = request.view_args.get('user_name')
    return user.name == user_name


def has_permission(permission):

    def permission_checker(user):
        if current_app.config.get('LOGIN_DISABLED'):
            return True
        permissions = []
        # Everyone gets base permissions
        permissions.extend(current_app.config.opsy['auth']['base_permissions'])
        if user.is_authenticated and user.is_active:
            # Logged in users get logged in permissions
            permissions.extend(
                current_app.config.opsy['auth']['logged_in_permissions'])
            # And a user gets their own permissions from their roles
            if hasattr(user, 'permissions'):
                permissions.extend([x.name for x in user.permissions])
        return permission in permissions

    return permission_checker


def need_permission(permission_name, *requirements, identity=None,
                    on_fail=None, throws=None):
    """Modified version of flask_allows requires decorator to tie into RBAC."""

    def decorator(func):

        permission = has_permission(permission_name)
        if requirements:
            new_requirements = (Or(permission, *requirements),)
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
