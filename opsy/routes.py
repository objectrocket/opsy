from flask import Blueprint
from flask_restful import Api
from opsy.views import (about, user_login, user_logout, AuthAPI, RoleAPI,
                        RolesAPI, UserAPI, UsersAPI, UserSettingAPI,
                        UserSettingsAPI)


core_site = Blueprint('core_site', __name__,  # pylint: disable=invalid-name
                      template_folder='templates',
                      static_url_path='/static',
                      static_folder='static')

core_site.add_url_rule(
    '/', endpoint='about', view_func=about)
core_site.add_url_rule(
    '/login', endpoint='user_login', view_func=user_login, methods=['POST'])
core_site.add_url_rule(
    '/logout', endpoint='user_logout', view_func=user_logout)

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
