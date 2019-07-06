from flask import abort, current_app, render_template, redirect, url_for, flash
from flask_allows import requires, Or
from flask_restful import Resource, reqparse
from flask_login import current_user
from opsy.access import (HasPermission, is_logged_in, is_same_user,
                         USERS_CREATE, USERS_READ, USERS_UPDATE, USERS_DELETE,
                         ROLES_CREATE, ROLES_READ, ROLES_UPDATE, ROLES_DELETE)
from opsy.auth import login, logout, create_token
from opsy.schema import (use_args_with, UserSchema, UserLoginSchema,
                         UserTokenSchema, UserSettingSchema, RoleSchema)
from opsy.models import User, Role
from opsy.exceptions import DuplicateError


def about():
    return render_template('about.html', title='About')


@use_args_with(UserLoginSchema, locations=('form',))
def user_login(args):
    user = login(args['user_name'], args['password'],
                 remember=args['remember_me'])
    if not user:
        flash('Username or password incorrect.')
        return redirect(url_for('core_site.about'))
    return redirect(url_for('core_site.about'))


@requires(is_logged_in)
def user_logout():
    logout(current_user)
    return redirect(url_for('core_site.about'))


class AuthAPI(Resource):

    @requires(is_logged_in)
    def get(self):  # pylint: disable=no-self-use
        create_token(current_user)
        return UserTokenSchema().jsonify(current_user)

    @use_args_with(UserLoginSchema, locations=('form', 'json'))
    def post(self, args):
        current_app.logger.info(args)
        user = login(args['user_name'], args['password'],
                     remember=args['remember_me'])
        if not user:
            abort(401, 'Username or password incorrect.')
        return UserTokenSchema().jsonify(current_user)

    @requires(is_logged_in)
    def delete(self):  # pylint: disable=no-self-use
        logout(current_user)
        return ('', 205)


class RolesAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name')
        self.reqparse.add_argument('ldap_group')
        self.reqparse.add_argument('description')
        super().__init__()

    @use_args_with(RoleSchema, as_kwargs=True)
    @requires(HasPermission(ROLES_CREATE))
    def post(self, **kwargs):
        try:
            role = Role.create(**kwargs)
        except (DuplicateError, ValueError) as error:
            abort(400, str(error))
        return RoleSchema().jsonify(role)

    @use_args_with(RoleSchema, as_kwargs=True)
    @requires(HasPermission(ROLES_READ))
    def get(self, **kwargs):
        roles = Role.query.filter_by(**kwargs)
        return RoleSchema(many=True).jsonify(roles)


class RoleAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super().__init__()

    @requires(HasPermission(ROLES_READ))
    def get(self, role_name):  # pylint: disable=no-self-use
        role = Role.query.filter_in(name=role_name).first()
        if not role:
            abort(403)
        return RoleSchema().jsonify(role)

    @requires(HasPermission(ROLES_UPDATE))
    def patch(self, role_name):
        self.reqparse.add_argument('name')
        self.reqparse.add_argument('ldap_group')
        self.reqparse.add_argument('description')
        args = self.reqparse.parse_args()
        role = Role.query.filter_in(name=role_name).first()
        if not role:
            abort(404)
        role.update(ignore_none=True, **args)
        return RoleSchema().jsonify(role)

    @requires(HasPermission(ROLES_DELETE))
    def delete(self, role_name):  # pylint: disable=no-self-use
        role = Role.query.filter_in(name=role_name).first()
        if not role:
            abort(404)
        role.delete()
        return ('', 202)


class UsersAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name')
        self.reqparse.add_argument('full_name')
        self.reqparse.add_argument('email')
        self.reqparse.add_argument('enabled')
        super().__init__()

    @requires(HasPermission(USERS_CREATE))
    def post(self):
        self.reqparse.replace_argument('name', required=True)
        args = self.reqparse.parse_args()
        try:
            user = User.create(**args)
        except (DuplicateError, ValueError) as error:
            abort(400, str(error))
        return UserSchema().jsonify(user)

    @requires(HasPermission(USERS_READ))
    def get(self):
        args = self.reqparse.parse_args()
        users = User.query.filter_in(ignore_none=True, **args)
        return UserSchema(many=True).jsonify(users)


class UserAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super().__init__()

    @requires(Or(HasPermission(USERS_READ), is_same_user))
    def get(self, user_name):  # pylint: disable=no-self-use
        user = User.query.filter_in(name=user_name).first()
        if not user:
            abort(403)
        return UserSchema().jsonify(user)

    @requires(Or(HasPermission(USERS_UPDATE), is_same_user))
    def patch(self, user_name):
        self.reqparse.add_argument('full_name')
        self.reqparse.add_argument('email')
        self.reqparse.add_argument('enabled')
        args = self.reqparse.parse_args()
        user = User.query.filter_in(name=user_name).first()
        if not user:
            abort(404)
        user.update(ignore_none=True, **args)
        return UserSchema().jsonify(user)

    @requires(HasPermission(USERS_DELETE))
    def delete(self, user_name):  # pylint: disable=no-self-use
        user = User.query.filter_in(name=user_name).first()
        if not user:
            abort(404)
        user.delete()
        return ('', 202)


class UserSettingsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('key')
        self.reqparse.add_argument('value')
        super().__init__()

    @requires(Or(HasPermission(USERS_UPDATE), is_same_user))
    def post(self, user_name):
        self.reqparse.replace_argument('key', required=True)
        self.reqparse.replace_argument('value', required=True)
        args = self.reqparse.parse_args()
        user = User.query.filter_in(name=user_name).first()
        if not user:
            abort(404)
        try:
            setting = user.add_setting(args['key'], args['value'])
        except DuplicateError as error:
            abort(400, str(error))
        return UserSettingSchema().jsonify(setting)

    @requires(Or(HasPermission(USERS_READ), is_same_user))
    def get(self, user_name):
        user = User.query.filter_in(name=user_name).first()
        if not user:
            abort(404)
        return UserSettingSchema(many=True).jsonify(user.settings)


class UserSettingAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('value', required=True, location='json')
        super().__init__()

    @requires(Or(HasPermission(USERS_UPDATE), is_same_user))
    def patch(self, user_name, setting_key):
        args = self.reqparse.parse_args()
        user = User.query.filter_in(name=user_name).first()
        if not user:
            abort(404)
        try:
            setting = user.modify_setting(setting_key, args['value'])
        except ValueError as error:
            abort(404, str(error))
        return UserSettingSchema().jsonify(setting)

    @requires(Or(HasPermission(USERS_READ), is_same_user))
    def get(self, user_name, setting_key):
        user = User.query.filter_in(name=user_name).first()
        if not user:
            abort(404)
        try:
            setting = user.get_setting(setting_key, error_on_none=True)
        except ValueError as error:
            abort(404, str(error))
        return UserSettingSchema().jsonify(setting)

    @requires(Or(HasPermission(USERS_UPDATE), is_same_user))
    def delete(self, user_name, setting_key):
        user = User.query.filter_in(name=user_name).first()
        if not user:
            abort(404)
        try:
            user.remove_setting(setting_key)
        except ValueError as error:
            abort(404, str(error))
        return ('', 202)
