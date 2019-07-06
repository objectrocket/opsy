from flask import abort, current_app, render_template, redirect, url_for, flash
from flask_allows import requires, Or
from flask_classful import route
from opsy.resources import Resource
from opsy.schema import use_args_with
from opsy.auth import login, logout, create_token
from opsy.auth.schema import (UserSchema, UserLoginSchema,
                         UserTokenSchema, UserSettingSchema, RoleSchema)
from opsy.auth.models import User, Role
from opsy.exceptions import DuplicateError


class RolesAPI(Resource):

    @use_args_with(RoleSchema, as_kwargs=True)
    def index(self, **kwargs):
        roles = Role.query.filter_by(**kwargs)
        return RoleSchema(many=True).jsonify(roles)

    @use_args_with(RoleSchema, as_kwargs=True)
    def post(self, **kwargs):
        try:
            role = Role.create(**kwargs)
        except (DuplicateError, ValueError) as error:
            abort(400, str(error))
        return RoleSchema().jsonify(role)

    def get(self, role_name):  # pylint: disable=no-self-use
        role = Role.query.filter_in(name=role_name).first()
        if not role:
            abort(403)
        return RoleSchema().jsonify(role)

    @use_args_with(RoleSchema, as_kwargs=True)
    def patch(self, role_name, **kwargs):
        args = self.reqparse.parse_args()
        role = Role.query.filter_in(name=role_name).first()
        if not role:
            abort(404)
        role.update(ignore_none=True, **args)
        return RoleSchema().jsonify(role)

    def delete(self, role_name):  # pylint: disable=no-self-use
        role = Role.query.filter_in(name=role_name).first()
        if not role:
            abort(404)
        role.delete()
        return ('', 202)
