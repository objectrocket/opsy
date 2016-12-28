from flask import abort, current_app, flash, redirect, request, Blueprint, jsonify, url_for
from flask_restful import Api, Resource, reqparse
from flask_login import current_user
from opsy.auth.access import permissions
from opsy.auth.models import User
from opsy.exceptions import DuplicateError


core_api = Blueprint('core_api', __name__, url_prefix='/api')  # pylint: disable=invalid-name
api = Api(core_api)  # pylint: disable=invalid-name


class Login(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('username', required=True, location=['form', 'json'])
        self.reqparse.add_argument('password', required=True, location=['form', 'json'])
        self.reqparse.add_argument('remember_me', type=bool, location='form')
        self.reqparse.add_argument('force_renew', type=bool, location='json')
        super().__init__()

    def get(self):  # pylint: disable=no-self-use
        if not permissions.get('logged_in').can():
            abort(401)
        return jsonify(current_user.get_session_token(current_app))

    def post(self):
        args = self.reqparse.parse_args()
        user = User.query.wtfilter_by(name=args['username']).first()
        if user and user.login(current_app, args['password'],
                               remember=args['remember_me']):
            if request.is_json:
                return jsonify(user.get_session_token(
                    current_app, force_renew=args['force_renew']))
            else:
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


class UsersAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name')
        self.reqparse.add_argument('full_name')
        self.reqparse.add_argument('email')
        self.reqparse.add_argument('enabled')
        super().__init__()

    def post(self):
        self.reqparse.replace_argument('name', required=True)
        args = self.reqparse.parse_args()
        if not permissions.get('users_create').can():
            abort(403)
        try:
            user = User.create(**args)
        except (DuplicateError, ValueError) as error:
            abort(400, str(error))
        return jsonify({'users': [user.get_dict()]})

    def get(self):
        args = self.reqparse.parse_args()
        if not permissions.get('users_read').can():
            abort(403)
        users = User.query.wtfilter_by(prune_none_values=True, **args).all_dict_out()
        return jsonify({'users': users})


class UserAPI(Resource):

    def get(self, user_name):  # pylint: disable=no-self-use
        user = User.query.wtfilter_by(name=user_name).first()
        if user and permissions.get('user_read')(user.id).can():
            return jsonify({'users': [user.get_dict()]})
        abort(403)

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
        return jsonify({'settings': user.settings.all_dict_out()})


class UserSettingAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('value', required=True, location='json')
        super().__init__()

    def post(self, user_name, setting_key):
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

api.add_resource(
    Login, '/login',
    endpoint='login')
api.add_resource(
    Logout, '/logout',
    endpoint='logout')
api.add_resource(
    UsersAPI, '/users',
    endpoint='users')
api.add_resource(
    UserAPI, '/users/<user_name>',
    endpoint='user')
api.add_resource(
    UserSettingsAPI, '/users/<user_name>/settings',
    endpoint='user_settings')
api.add_resource(
    UserSettingAPI, '/users/<user_name>/settings/<setting_key>',
    endpoint='user_setting')
