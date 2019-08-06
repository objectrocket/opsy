from flask import abort, Blueprint
from flask_apispec import marshal_with, doc
from opsy.flask_extensions import apispec
from opsy.rbac import need_permission
from opsy.schema import use_kwargs, EmptySchema
from opsy.inventory.schema import (
    ZoneSchema, ZoneQuerySchema,
    HostSchema, HostQuerySchema,
    GroupSchema, GroupQuerySchema,
    HostGroupMappingSchema, HostGroupMappingQuerySchema)
from opsy.inventory.models import Zone, Host, Group, HostGroupMapping
from opsy.exceptions import DuplicateError


def create_inventory_views(app):
    app.register_blueprint(zones_blueprint, url_prefix='/api/v1/zones')
    app.register_blueprint(hosts_blueprint, url_prefix='/api/v1/hosts')
    app.register_blueprint(groups_blueprint, url_prefix='/api/v1/groups')
    apispec.spec.tag(
        {'name': 'zones',
         'description': 'Zones are the base grouping for inventory in Opsy.'})
    for view in [zones_list, zones_post, zones_get, zones_patch,
                 zones_delete]:
        apispec.register(view, blueprint='inventory_zones')
    apispec.spec.tag(
        {'name': 'hosts',
         'description': 'Hosts are your servers.'})
    for view in [hosts_list, hosts_post, hosts_get, hosts_patch, hosts_delete,
                 host_group_mappings_list, host_group_mappings_post,
                 host_group_mappings_get, host_group_mappings_patch,
                 host_group_mappings_delete]:
        apispec.register(view, blueprint='inventory_hosts')
    app.config['APISPEC_SPEC'].tag(
        {'name': 'groups',
         'description': 'Groups are logical groupings of your hosts.'})
    for view in [groups_list, groups_post, groups_get, groups_patch,
                 groups_delete]:
        apispec.register(view, blueprint='inventory_groups')

###############################################################################
# Blueprints
###############################################################################


# pylint: disable=invalid-name
zones_blueprint = Blueprint('inventory_zones', __name__)
# pylint: disable=invalid-name
hosts_blueprint = Blueprint('inventory_hosts', __name__)
# pylint: disable=invalid-name
groups_blueprint = Blueprint('inventory_groups', __name__)

###############################################################################
# Zone Views
###############################################################################


@zones_blueprint.route('/', methods=['GET'])
@use_kwargs(ZoneQuerySchema, locations=['query'])
@marshal_with(ZoneSchema(many=True), code=200)
@doc(
    operationId='list_zones',
    summary='List zones.',
    description='',
    tags=['zones'],
    security=[{'api_key': []}])
@need_permission('list_zones')
def zones_list(**kwargs):
    return Zone.query.filter_in(**kwargs).all()


@zones_blueprint.route('/', methods=['POST'])
@use_kwargs(ZoneSchema)
@marshal_with(ZoneSchema(), code=201)
@doc(
    operationId='create_zone',
    summary='Create a new zone.',
    description='',
    tags=['zones'],
    security=[{'api_key': []}])
@need_permission('create_zone')
def zones_post(**kwargs):
    try:
        return Zone.create(**kwargs), 201
    except (DuplicateError, ValueError) as error:
        abort(400, str(error))


@zones_blueprint.route('/<id_or_name>', methods=['GET'])
@marshal_with(ZoneSchema(), code=200)
@doc(
    operationId='show_zone',
    summary='Show a zone.',
    description='',
    tags=['zones'],
    security=[{'api_key': []}])
@need_permission('show_zone')
def zones_get(id_or_name):
    zone = Zone.get_by_id_or_name(id_or_name)
    if not zone:
        abort(404)
    return zone


@zones_blueprint.route('/<id_or_name>', methods=['PATCH'])
@use_kwargs(ZoneSchema)
@marshal_with(ZoneSchema(), code=200)
@doc(
    operationId='update_zone',
    summary='Update a zone.',
    description='',
    tags=['zones'],
    security=[{'api_key': []}])
@need_permission('update_zone')
def zones_patch(id_or_name, **kwargs):
    zone = Zone.get_by_id_or_name(id_or_name)
    if not zone:
        abort(404)
    zone.update(**kwargs)
    return zone


@zones_blueprint.route('/<id_or_name>', methods=['DELETE'])
@marshal_with(EmptySchema, code=204)
@doc(
    operationId='delete_zone',
    summary='Delete a zone.',
    description='',
    tags=['zones'],
    security=[{'api_key': []}])
@need_permission('delete_zone')
def zones_delete(id_or_name):
    zone = Zone.get_by_id_or_name(id_or_name)
    if not zone:
        abort(404)
    zone.delete()
    return ('', 204)

###############################################################################
# Host Views
###############################################################################


@hosts_blueprint.route('/', methods=['GET'])
@use_kwargs(HostQuerySchema, locations=['query'])
@marshal_with(HostSchema(many=True), code=200)
@doc(
    operationId='list_hosts',
    summary='List hosts.',
    description='',
    tags=['hosts'],
    security=[{'api_key': []}])
@need_permission('list_hosts')
def hosts_list(**kwargs):
    return Host.query.filter_in(**kwargs).all()


@hosts_blueprint.route('/', methods=['POST'])
@use_kwargs(HostSchema)
@marshal_with(HostSchema(), code=201)
@doc(
    operationId='create_host',
    summary='Create a new host.',
    description='',
    tags=['hosts'],
    security=[{'api_key': []}])
@need_permission('create_host')
def hosts_post(**kwargs):
    try:
        return Host.create(**kwargs), 201
    except (DuplicateError, ValueError) as error:
        abort(400, str(error))


@hosts_blueprint.route('/<id_or_name>', methods=['GET'])
@marshal_with(HostSchema(), code=200)
@doc(
    operationId='show_host',
    summary='Show a host.',
    description='',
    tags=['hosts'],
    security=[{'api_key': []}])
@need_permission('show_host')
def hosts_get(id_or_name):
    host = Host.get_by_id_or_name(id_or_name)
    if not host:
        abort(404)
    return host


@hosts_blueprint.route('/<id_or_name>', methods=['PATCH'])
@use_kwargs(HostSchema)
@marshal_with(HostSchema(), code=200)
@doc(
    operationId='update_host',
    summary='Update a host.',
    description='',
    tags=['hosts'],
    security=[{'api_key': []}])
@need_permission('update_host')
def hosts_patch(id_or_name, **kwargs):
    host = Host.get_by_id_or_name(id_or_name)
    if not host:
        abort(404)
    host.update(**kwargs)
    return host


@hosts_blueprint.route('/<id_or_name>', methods=['DELETE'])
@marshal_with(EmptySchema, code=204)
@doc(
    operationId='delete_host',
    summary='Delete a host.',
    description='',
    tags=['hosts'],
    security=[{'api_key': []}])
@need_permission('delete_host')
def hosts_delete(id_or_name):
    host = Host.get_by_id_or_name(id_or_name)
    if not host:
        abort(404)
    host.delete()
    return ('', 204)

###############################################################################
# Host Group Mapping Views
###############################################################################


@hosts_blueprint.route('/<id_or_name>/group_mappings', methods=['GET'])
@use_kwargs(HostGroupMappingQuerySchema, locations=['query'])
@marshal_with(HostGroupMappingSchema(many=True), code=200)
@doc(
    operationId='list_group_mappings',
    summary='List group mappings.',
    description='',
    tags=['hosts'],
    security=[{'api_key': []}])
@need_permission('update_host')
def host_group_mappings_list(id_or_name, **kwargs):
    host = Host.get_by_id_or_name(id_or_name)
    if not host:
        abort(404)
    return HostGroupMapping.query.join(Host).filter(
        Host.id == host.id).filter_in(**kwargs)


@hosts_blueprint.route('/<id_or_name>/group_mappings', methods=['POST'])
@use_kwargs(HostGroupMappingSchema)
@marshal_with(HostGroupMappingSchema(), code=201)
@doc(
    operationId='create_group_mapping',
    summary='Create a group mapping.',
    description='',
    tags=['hosts'],
    security=[{'api_key': []}])
@need_permission('update_host')
def host_group_mappings_post(id_or_name, **kwargs):
    host = Host.get_by_id_or_name(id_or_name)
    group = Group.get_by_id(kwargs['group_id'])
    try:
        return host.add_group(group, priority=kwargs.get('priority')), 201
    except (DuplicateError, ValueError) as error:
        abort(400, str(error))


@hosts_blueprint.route(
    '/<id_or_name>/group_mappings/<mapping_id>',
    methods=['GET'])
@marshal_with(HostGroupMappingSchema(), code=200)
@doc(
    operationId='show_group_mapping',
    summary='Show a group mapping.',
    description='',
    tags=['hosts'],
    security=[{'api_key': []}])
@need_permission('update_host')
def host_group_mappings_get(id_or_name, mapping_id):
    host_group_mapping = HostGroupMapping.get_by_id(mapping_id)
    if not host_group_mapping:
        abort(404)
    return host_group_mapping


@hosts_blueprint.route(
    '/<id_or_name>/group_mappings/<mapping_id>',
    methods=['PATCH'])
@use_kwargs(HostGroupMappingSchema)
@marshal_with(HostGroupMappingSchema(), code=200)
@doc(
    operationId='update_group_mapping',
    summary='Update a group mapping.',
    description='',
    tags=['hosts'],
    security=[{'api_key': []}])
@need_permission('update_host')
def host_group_mappings_patch(id_or_name, mapping_id, **kwargs):
    host_group_mapping = HostGroupMapping.get_by_id(mapping_id)
    if not host_group_mapping:
        abort(404)
    host_group_mapping.update(**kwargs)
    return host_group_mapping


@hosts_blueprint.route(
    '/<id_or_name>/group_mappings/<mapping_id>',
    methods=['DELETE'])
@marshal_with(EmptySchema, code=204)
@doc(
    operationId='delete_group_mapping',
    summary='Delete a group mapping.',
    description='',
    tags=['hosts'],
    security=[{'api_key': []}])
@need_permission('update_host')
def host_group_mappings_delete(id_or_name, mapping_id):
    host_group_mapping = HostGroupMapping.get_by_id(mapping_id)
    if not host_group_mapping:
        abort(404)
    host_group_mapping.delete()
    return ('', 204)


###############################################################################
# Group Views
###############################################################################


@groups_blueprint.route('/', methods=['GET'])
@use_kwargs(GroupQuerySchema, locations=['query'])
@marshal_with(GroupSchema(many=True), code=200)
@doc(
    operationId='list_groups',
    summary='List groups.',
    description='',
    tags=['groups'],
    security=[{'api_key': []}])
@need_permission('list_groups')
def groups_list(**kwargs):
    return Group.query.filter_in(**kwargs).all()


@groups_blueprint.route('/', methods=['POST'])
@use_kwargs(GroupSchema)
@marshal_with(GroupSchema(), code=201)
@doc(
    operationId='create_group',
    summary='Create a group.',
    description='',
    tags=['groups'],
    security=[{'api_key': []}])
@need_permission('create_group')
def groups_post(**kwargs):
    try:
        return Group.create(**kwargs), 201
    except (DuplicateError, ValueError) as error:
        abort(400, str(error))


@groups_blueprint.route('/<id_or_name>', methods=['GET'])
@marshal_with(GroupSchema(), code=200)
@doc(
    operationId='show_group',
    summary='Show a group.',
    description='',
    tags=['groups'],
    security=[{'api_key': []}])
@need_permission('show_group')
def groups_get(id_or_name):
    group = Group.get_by_id_or_name(id_or_name)
    if not group:
        abort(404)
    return group


@groups_blueprint.route('/<id_or_name>', methods=['PATCH'])
@use_kwargs(GroupSchema)
@marshal_with(GroupSchema(), code=200)
@doc(
    operationId='update_group',
    summary='Update a group.',
    description='',
    tags=['groups'],
    security=[{'api_key': []}])
@need_permission('update_group')
def groups_patch(id_or_name, **kwargs):
    group = Group.get_by_id_or_name(id_or_name)
    if not group:
        abort(404)
    group.update(**kwargs)
    return group


@groups_blueprint.route('/<id_or_name>', methods=['DELETE'])
@marshal_with(EmptySchema, code=204)
@doc(
    operationId='delete_group',
    summary='Delete a group.',
    description='',
    tags=['groups'],
    security=[{'api_key': []}])
@need_permission('delete_group')
def groups_delete(id_or_name):
    group = Group.get_by_id_or_name(id_or_name)
    if not group:
        abort(404)
    group.delete()
    return ('', 204)
