from collections import namedtuple
from functools import wraps
from flask import current_app, request
from flask_allows import allows, Or, Requirement
from flask_apispec import ResourceMeta
from flask_classful import FlaskView, get_interesting_members, \
    _dashify_uppercase
from opsy.utils import merge_dict


Need = namedtuple(  # pylint: disable=invalid-name
    'Need', ['name', 'resource', 'description'])


def is_logged_in(user):
    if current_app.config.get('LOGIN_DISABLED') or user.is_authenticated:
        return True
    return False


def is_same_user(user):
    """Checks if the user is the same user in the request."""
    user_name = request.view_args.get('user_name')
    return user.name == user_name


def rbac(*requirements, resource_name=None, **opts):
    """
    This is a modified version of flask_allows requirement decorator to tie
    into Opsy's RBAC system.
    """

    identity = opts.get("identity")
    on_fail = opts.get("on_fail")
    throws = opts.get("throws")

    def decorator(f):

        @wraps(f)
        def allower(*args, **kwargs):
            if resource_name:
                need = f'{resource_name}_{f.__name__}'
                if requirements:
                    new_requirements = (Or(HasPermission(need), requirements))
                else:
                    new_requirements = (HasPermission(need),)
            else:
                new_requirements = requirements

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
            return f(*args, **kwargs)
        allower.__rbac__ = True
        return allower
    return decorator


def no_rbac(func):
    func.__rbac__ = False
    return func


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
        return self.permission in permissions or 'god_mode' in permissions


class Resource(FlaskView, metaclass=ResourceMeta):

    resource_name = None
    no_rbac = False
    _needs = None

    @classmethod
    def register(cls, *args, **kwargs):
        cls.resource_name = cls.build_resource_name()
        needs = {}
        for verb, value in get_interesting_members(Resource, cls):
            # iterate through the routes and add their dynamic needs
            method = getattr(cls, verb)
            if not getattr(method, '__rbac__', True):
                # No rbac for this endpoint
                continue
            need = Need(
                f'{cls.resource_name}_{verb}',
                cls.resource_name,
                f'Ability to "{verb}" against {cls.resource_name}.')
            needs[verb] = need
        cls._needs = {cls.resource_name: needs}
        super().register(*args, **kwargs)

    @classmethod
    def default_route_base(cls):
        if cls.__name__.endswith("View"):
            route_base = _dashify_uppercase(cls.__name__[:-4])
        elif cls.__name__.endswith("API"):
            route_base = _dashify_uppercase(cls.__name__[:-3])
        else:
            route_base = _dashify_uppercase(cls.__name__)
        return route_base

    @classmethod
    def make_proxy_method(cls, name, *args):
        """
        We add some additional logic to this method to inject our rbac
        decorator on a per-method basis.
        """
        method = getattr(cls, name)
        if cls.no_rbac or hasattr(method, '__rbac__'):
            # We skip if the class has rbac disabled or if the method
            # has already been touched.
            return super().make_proxy_method(name, *args)
        resource_name = cls.build_resource_name()
        cls.decorators.insert(0, rbac(resource_name=resource_name))
        proxy = super().make_proxy_method(name, *args)
        cls.decorators.pop(0)
        return proxy

    @classmethod
    def build_resource_name(cls):
        return cls.resource_name or cls.get_route_base()


class ResourceManager(object):

    def __init__(self, app=None, docs=None, route_prefix=None):
        self.app = app
        self.registry = []
        self.docs = docs
        self._needs_catalog = None
        self.route_prefix = route_prefix
        if app:
            self.init_app(app)

    def init_app(self, app, docs=None):
        self.app = app
        if docs:
            self.docs = docs

    def add_resource(self, resource):
        if not self.app:
            raise ValueError('ResourceManager must be registered with an app.')
        resource.route_prefix = self.route_prefix
        self.registry.append(resource)
        resource.register(self.app)
        if self.docs:
            for name, value in get_interesting_members(Resource, resource):
                self.docs.register(
                    resource, endpoint=resource.build_route_name(name))

    @property
    def needs_catalog(self):
        if self._needs_catalog:
            return self._needs_catalog
        catalog = {}
        for klass in self.registry:
            merge_dict(catalog, klass._needs)
        self._needs_catalog = catalog
        return catalog

    def get_needs(self, resource=None, method=None):
        needs_list = [
            Need('god_mode', 'all', 'Unlimited access to everything.')]
        needs = self.needs_catalog
        if resource:
            needs = {k: v for k, v in needs.items() if k == resource}
        if method:
            needs = {k: {method: v[method]} for k, v in needs.items()}
        for value in needs.values():
            for need in value.values():
                needs_list.append(need)
        return needs_list
