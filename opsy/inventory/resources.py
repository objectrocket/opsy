from flask import abort
from opsy.flask_extensions import db
from opsy.resources import Resource
from opsy.schema import use_args_with
from opsy.inventory.schema import (ZoneSchema, HostSchema, GroupSchema,
                                   HostGroupMappingSchema)
from opsy.inventory.models import Zone, Host, Group, HostGroupMapping
from opsy.exceptions import DuplicateError


class ZonesAPI(Resource):

    @use_args_with(ZoneSchema, as_kwargs=True)
    def index(self, **kwargs):
        zones = Zone.query.filter_in(**kwargs)
        return ZoneSchema(many=True).jsonify(zones)

    @use_args_with(ZoneSchema, as_kwargs=True)
    def post(self, **kwargs):
        try:
            zone = Zone.create(**kwargs)
        except (DuplicateError, ValueError) as error:
            abort(400, str(error))
        return ZoneSchema().jsonify(zone)

    def get(self, id_or_name):  # pylint: disable=no-self-use
        zone = Zone.get_by_id_or_name(id_or_name)
        if not zone:
            abort(403)
        return ZoneSchema().jsonify(zone)

    @use_args_with(ZoneSchema, as_kwargs=True)
    def patch(self, id_or_name, **kwargs):
        zone = Zone.get_by_id_or_name(id_or_name)
        if not zone:
            abort(404)
        zone.update(**kwargs)
        return ZoneSchema().jsonify(zone)

    def delete(self, id_or_name):  # pylint: disable=no-self-use
        zone = Zone.get_by_id_or_name(id_or_name)
        if not zone:
            abort(404)
        zone.delete()
        return ('', 202)


class HostsAPI(Resource):

    @use_args_with(HostSchema, as_kwargs=True)
    def index(self, **kwargs):
        hosts = Host.query.filter_in(**kwargs)
        return HostSchema(many=True).jsonify(hosts)

    @use_args_with(HostSchema, as_kwargs=True)
    def post(self, **kwargs):
        try:
            host = Host.create(**kwargs)
        except (DuplicateError, ValueError) as error:
            abort(400, str(error))
        return HostSchema().jsonify(host)

    def get(self, id_or_name):  # pylint: disable=no-self-use
        host = Host.get_by_id_or_name(id_or_name)
        if not host:
            abort(403)
        return HostSchema().jsonify(host)

    @use_args_with(HostSchema, as_kwargs=True)
    def patch(self, id_or_name, **kwargs):
        host = Host.get_by_id_or_name(id_or_name)
        if not host:
            abort(404)
        host.update(**kwargs)
        return HostSchema().jsonify(host)

    def delete(self, id_or_name):  # pylint: disable=no-self-use
        host = Host.get_by_id_or_name(id_or_name)
        if not host:
            abort(404)
        host.delete()
        return ('', 202)


class HostGroupMappingsAPI(Resource):

    route_base = '/hosts/<host_id_or_name>/groups/'
    resource_name = 'host_group_mappings'

    @use_args_with(HostGroupMappingSchema, as_kwargs=True)
    def index(self, host_id_or_name, **kwargs):
        host_group_mappings = HostGroupMapping.query.join(Host).filter(
            db.or_(Host.name == host_id_or_name,
                   Host.id == host_id_or_name)).filter_in(**kwargs)
        return HostGroupMappingSchema(many=True).jsonify(host_group_mappings)

    @use_args_with(HostGroupMappingSchema, as_kwargs=True)
    def post(self, host_id_or_name, **kwargs):
        host = Host.get_by_id_or_name(host_id_or_name)
        group = Group.get_by_id_or_name(kwargs['group_id'])
        try:
            host_group_mapping = host.add_group(
                group, priority=kwargs.get('priority'))
        except (DuplicateError, ValueError) as error:
            abort(400, str(error))
        return HostGroupMappingSchema().jsonify(host_group_mapping)

    def get(self, host_id_or_name, host_group_mapping_id):
        host_group_mapping = HostGroupMapping.get_by_id(host_group_mapping_id)
        if not host_group_mapping:
            abort(403)
        return HostGroupMappingSchema().jsonify(host_group_mapping)

    @use_args_with(HostGroupMappingSchema, as_kwargs=True)
    def patch(self, host_id_or_name, host_group_mapping_id, **kwargs):
        host_group_mapping = HostGroupMapping.get_by_id(host_group_mapping_id)
        if not host_group_mapping:
            abort(404)
        host_group_mapping.update(**kwargs)
        return HostGroupMappingSchema().jsonify(host_group_mapping)

    def delete(self, host_id_or_name, host_group_mapping_id):
        host_group_mapping = HostGroupMapping.get_by_id(host_group_mapping_id)
        if not host_group_mapping:
            abort(404)
        host_group_mapping.delete()
        return ('', 202)


class GroupsAPI(Resource):

    @use_args_with(GroupSchema, as_kwargs=True)
    def index(self, **kwargs):
        groups = Group.query.filter_in(**kwargs)
        return GroupSchema(many=True).jsonify(groups)

    @use_args_with(GroupSchema, as_kwargs=True)
    def post(self, **kwargs):
        try:
            group = Group.create(**kwargs)
        except (DuplicateError, ValueError) as error:
            abort(400, str(error))
        return GroupSchema().jsonify(group)

    def get(self, id_or_name):  # pylint: disable=no-self-use
        group = Group.get_by_id_or_name(id_or_name)
        if not group:
            abort(403)
        return GroupSchema().jsonify(group)

    @use_args_with(GroupSchema, as_kwargs=True)
    def patch(self, id_or_name, **kwargs):
        group = Group.get_by_id_or_name(id_or_name)
        if not group:
            abort(404)
        group.update(**kwargs)
        return GroupSchema().jsonify(group)

    def delete(self, id_or_name):  # pylint: disable=no-self-use
        group = Group.get_by_id_or_name(id_or_name)
        if not group:
            abort(404)
        group.delete()
        return ('', 202)
