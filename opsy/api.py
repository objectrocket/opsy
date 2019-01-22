from flask import Blueprint
from flask_restful import Api
from opsy.resources import (AuthAPI, RoleAPI, RolesAPI, UserAPI, UsersAPI,
                            UserSettingAPI, UserSettingsAPI)


core_api = Blueprint(  # pylint: disable=invalid-name
    'core_api', __name__, url_prefix='/api')
api = Api(core_api)  # pylint: disable=invalid-name

api.add_resource(
    AuthAPI, '/auth',
    endpoint='auth')
api.add_resource(
    RolesAPI, '/roles',
    endpoint='roles')
api.add_resource(
    RoleAPI, '/roles/<role_name>',
    endpoint='role')
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
