from flask import abort, current_app, request, Blueprint, jsonify
from flask_restful import Api, Resource, reqparse
from flask_login import login_user, current_user
from flask_principal import identity_changed, Identity
from opsy.auth.access import permissions
from opsy.auth.models import User


core_api = Blueprint('core_api', __name__, url_prefix='/api')  # pylint: disable=invalid-name
api = Api(core_api)  # pylint: disable=invalid-name


class Login(Resource):

    def get(self):  # pylint: disable=no-self-use
        if not permissions.get('logged_in').can():
            abort(401)
        return "hello %s" % current_user.name

    def post(self):
        if request.is_json:
            username = request.get_json().get('username')
            password = request.get_json().get('password')
            force_renew = request.get_json().get('force_renew')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            force_renew = request.form.get('force_renew')
        if not (username and password):
            abort(401)
        user = User.get(name=username).first()
        if user and user.verify_password(password) and user.is_active:
            login_user(user)
            identity_changed.send(
                current_app._get_current_object(),  # pylint: disable=W0212
                identity=Identity(user.id))
            return jsonify(user.get_session_token(current_app,
                                                  force_renew=force_renew))
        else:
            abort(401)


class UsersAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('user_name')
        self.reqparse.add_argument('email')
        super().__init__()

    def get(self):
        args = self.reqparse.parse_args()
        if not permissions.get('read_users').can():
            abort(403)
        users = User.get(prune_none_values=True, name=args['user_name'],
                         email=args['email']).all_dict_out()
        return jsonify({'users': users})


class UserAPI(Resource):

    def get(self, user_name):  # pylint: disable=no-self-use
        user = User.get(name=user_name).first()
        if user and permissions.get('read_user')(user.id).can():
            return jsonify({'users': [user.get_dict()]})
        abort(403)


class UserSettingsAPI(Resource):

    def get(self, user_name):
        user = User.get(name=user_name).first()
        if not (user and permissions.get('read_user')(user.id).can()):
            abort(403)
        return jsonify({'settings': user.settings.all_dict_out()})


class UserSettingAPI(Resource):

    def post(self, user_name, setting_key):
        user = User.get(name=user_name).first()
        if not (user and permissions.get('read_user')(user.id).can()):
            abort(403)
        try:
            setting = user.get_setting(setting_key, error_on_none=True)
        except ValueError:
            abort(404)
        return jsonify({'settings': [setting.get_dict()]})

    def get(self, user_name, setting_key):
        user = User.get(name=user_name).first()
        if not (user and permissions.get('read_user')(user.id).can()):
            abort(403)
        try:
            setting = user.get_setting(setting_key, error_on_none=True)
        except ValueError:
            abort(404)
        return jsonify({'settings': [setting.get_dict()]})

    def delete(self, user_name, setting_key):
        user = User.get(name=user_name).first()
        if not (user and permissions.get('read_user')(user.id).can()):
            abort(403)
        try:
            user.remove_setting(setting_key)
        except ValueError:
            abort(404)
        return abort(202)

api.add_resource(
    Login, '/login',
    endpoint='login')
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
