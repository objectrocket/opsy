from flask import (abort, current_app, flash, redirect, request, jsonify,
                   url_for)
from flask_restful import Resource, reqparse
from flask_login import current_user
from opsy.access import permissions
from opsy.models import User, Role
from opsy.exceptions import DuplicateError


class Login(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('username', required=True,
                                   location=['form', 'json'])
        self.reqparse.add_argument('password', required=True,
                                   location=['form', 'json'])
        self.reqparse.add_argument('remember_me', type=bool, location='form')
        self.reqparse.add_argument('force_renew', type=bool, location='json')
        super().__init__()

    def get(self):  # pylint: disable=no-self-use
        if not permissions.get('logged_in').can():
            abort(401)
        return jsonify(current_user.get_session_token(current_app))

    def post(self):  # pylint: disable=inconsistent-return-statements
        args = self.reqparse.parse_args()
        token = User.login(current_app, args['username'], args['password'],
                           remember=args['remember_me'])
        if token:
            if request.is_json:
                return jsonify(token)
            return redirect(url_for('core_main.about'))
        elif request.is_json:
            abort(401, 'Username or password incorrect.')
        else:
            flash('Username or password incorrect.')
            return redirect(url_for('core_main.about'))


class Logout(Resource):

    def get(self):  # pylint: disable=no-self-use
        current_user.logout(current_app)
        return redirect(url_for('core_main.about'))


class RolesAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name')
        self.reqparse.add_argument('ldap_group')
        self.reqparse.add_argument('description')
        super().__init__()

    def post(self):
        self.reqparse.replace_argument('name', required=True)
        args = self.reqparse.parse_args()
        if not permissions.get('roles_create').can():
            abort(403)
        try:
            role = Role.create(**args)
        except (DuplicateError, ValueError) as error:
            abort(400, str(error))
        return jsonify({'roles': [role.get_dict()]})

    def get(self):
        args = self.reqparse.parse_args()
        if not permissions.get('roles_read').can():
            abort(403)
        roles = Role.query.wtfilter_by(prune_none_values=True,
                                       **args).all_dict_out()
        return jsonify({'roles': roles})


class RoleAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super().__init__()

    def get(self, role_name):  # pylint: disable=no-self-use,inconsistent-return-statements
        role = Role.query.wtfilter_by(name=role_name).first()
        if role and permissions.get('roles_read').can():
            return jsonify({'roles': [role.get_dict()]})
        abort(403)

    def patch(self, role_name):
        if not permissions.get('roles_update').can():
            abort(403)
        self.reqparse.add_argument('name')
        self.reqparse.add_argument('ldap_group')
        self.reqparse.add_argument('description')
        args = self.reqparse.parse_args()
        role = Role.query.wtfilter_by(name=role_name).first()
        if not role:
            abort(404)
        role.update(prune_none_values=True, **args)
        return jsonify({'roles': [role.get_dict()]})

    def delete(self, role_name):  # pylint: disable=no-self-use
        if not permissions.get('roles_delete').can():
            abort(403)
        role = Role.query.wtfilter_by(name=role_name).first()
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

    def post(self):
        if not permissions.get('users_create').can():
            abort(403)
        self.reqparse.replace_argument('name', required=True)
        args = self.reqparse.parse_args()
        try:
            user = User.create(**args)
        except (DuplicateError, ValueError) as error:
            abort(400, str(error))
        return jsonify({'users': [user.get_dict()]})

    def get(self):
        if not permissions.get('users_read').can():
            abort(403)
        args = self.reqparse.parse_args()
        users = User.query.wtfilter_by(prune_none_values=True, **args).all_dict_out()
        return jsonify({'users': users})


class UserAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super().__init__()

    def get(self, user_name):  # pylint: disable=no-self-use,inconsistent-return-statements
        user = User.query.wtfilter_by(name=user_name).first()
        if user and permissions.get('user_read')(user.id).can():
            return jsonify({'users': [user.get_dict()]})
        abort(403)

    def patch(self, user_name):
        self.reqparse.add_argument('full_name')
        self.reqparse.add_argument('email')
        self.reqparse.add_argument('enabled')
        args = self.reqparse.parse_args()
        user = User.query.wtfilter_by(name=user_name).first()
        if not (user and permissions.get('user_update')(user.id).can()):
            abort(403)
        user.update(prune_none_values=True, **args)
        return jsonify({'users': [user.get_dict()]})

    def delete(self, user_name):  # pylint: disable=no-self-use
        if not permissions.get('users_delete').can():
            abort(403)
        user = User.query.wtfilter_by(name=user_name).first()
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

    def post(self, user_name):
        self.reqparse.replace_argument('key', required=True)
        self.reqparse.replace_argument('value', required=True)
        args = self.reqparse.parse_args()
        user = User.query.wtfilter_by(name=user_name).first()
        if not (user and permissions.get('user_update')(user.id).can()):
            abort(403)
        try:
            setting = user.add_setting(args['key'], args['value'])
        except DuplicateError as error:
            abort(400, str(error))
        return jsonify({'settings': [setting.get_dict()]})

    def get(self, user_name):
        user = User.query.wtfilter_by(name=user_name).first()
        if not (user and permissions.get('user_read')(user.id).can()):
            abort(403)
        return jsonify({'settings': [x.get_dict() for x in user.settings]})


class UserSettingAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('value', required=True, location='json')
        super().__init__()

    def patch(self, user_name, setting_key):
        args = self.reqparse.parse_args()
        user = User.query.wtfilter_by(name=user_name).first()
        if not (user and permissions.get('user_update')(user.id).can()):
            abort(403)
        try:
            setting = user.modify_setting(setting_key, args['value'])
        except ValueError as error:
            abort(404, str(error))
        return jsonify({'settings': [setting.get_dict()]})

    def get(self, user_name, setting_key):
        user = User.query.wtfilter_by(name=user_name).first()
        if not (user and permissions.get('user_read')(user.id).can()):
            abort(403)
        try:
            setting = user.get_setting(setting_key, error_on_none=True)
        except ValueError as error:
            abort(404, str(error))
        return jsonify({'settings': [setting.get_dict()]})

    def delete(self, user_name, setting_key):
        user = User.query.wtfilter_by(name=user_name).first()
        if not (user and permissions.get('user_update')(user.id).can()):
            abort(403)
        try:
            user.remove_setting(setting_key)
        except ValueError as error:
            abort(404, str(error))
        return ('', 202)
