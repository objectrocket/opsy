from marshmallow import RAISE
from marshmallow import fields as ma_fields
from marshmallow_sqlalchemy import field_for
from opsy.inventory.models import Zone, Host, Group, HostGroupMapping
from opsy.flask_extensions import ma
from opsy.schema import BaseSchema

###############################################################################
# Sqlalchemy schemas
###############################################################################


class ZoneSchema(BaseSchema):

    class Meta:
        model = Zone
        fields = ('id', 'name', 'description', 'vars', 'created_at',
                  'updated_at', '_links')
        ordered = True
        unknown = RAISE

    id = field_for(Zone, 'id', dump_only=True)
    name = field_for(Zone, 'name', required=True)
    created_at = field_for(Zone, 'created_at', dump_only=True)
    updated_at = field_for(Zone, 'updated_at', dump_only=True)
    _links = ma.Hyperlinks(
        {"self": ma.URLFor("ZonesAPI:get", id_or_name="<id>"),
         "collection": ma.URLFor("ZonesAPI:index")}
    )


class ZoneRefSchema(ZoneSchema):

    class Meta:
        model = Zone
        fields = ('id', 'name', '_links')
        ordered = True
        unknown = RAISE


class HostSchema(BaseSchema):

    class Meta:
        model = Host
        fields = ('id', 'zone_id', 'name', 'domain', 'manufacturer', 'model',
                  'cpu_arch', 'cpu_model', 'cpu_count', 'cpu_flags', 'memory',
                  'swap', 'kernel', 'os', 'os_family', 'os_version',
                  'os_codename', 'os_arch', 'init_system', 'disks',
                  'networking', 'vars', 'compiled_vars', 'facts', 'zone',
                  'groups', 'created_at', 'updated_at', '_links')
        ordered = True
        unknown = RAISE

    id = field_for(Host, 'id', dump_only=True)
    name = field_for(Host, 'name', required=True)
    zone_id = field_for(Host, 'zone_id', required=True)
    created_at = field_for(Host, 'created_at', dump_only=True)
    updated_at = field_for(Host, 'updated_at', dump_only=True)
    compiled_vars = ma_fields.Dict(dump_only=True)
    # compiled_vars = field_for(Host, 'compiled_vars', dump_only=True)

    zone = ma.Nested(  # pylint: disable=no-member
        'ZoneRefSchema', dump_only=True)
    groups = ma.Nested(  # pylint: disable=no-member
        'HostGroupMappingRefSchema', attribute='group_mappings',
        dump_only=True, many=True)

    _links = ma.Hyperlinks(
        {"self": ma.URLFor("HostsAPI:get", id_or_name="<id>"),
         "collection": ma.URLFor("HostsAPI:index")}
    )


class HostRefSchema(HostSchema):

    class Meta:
        model = Host
        fields = ('id', 'name', '_links')
        ordered = True
        unknown = RAISE


class GroupSchema(BaseSchema):

    class Meta:
        model = Group
        fields = ('id', 'zone_id', 'parent_id', 'name', 'default_priority',
                  'vars', 'compiled_vars', 'zone', 'parent', 'created_at',
                  'updated_at', '_links')
        ordered = True
        unknown = RAISE

    id = field_for(Host, 'id', dump_only=True)
    created_at = field_for(Host, 'created_at', dump_only=True)
    updated_at = field_for(Host, 'updated_at', dump_only=True)
    compiled_vars = ma_fields.Dict(dump_only=True)
    zone = ma.Nested(  # pylint: disable=no-member
        'ZoneRefSchema', dump_only=True)
    parent = ma.Nested(  # pylint: disable=no-member
        'GroupRefSchema', dump_only=True)

    _links = ma.Hyperlinks(
        {"self": ma.URLFor("GroupsAPI:get", id_or_name="<id>"),
         "collection": ma.URLFor("GroupsAPI:index")}
    )


class GroupRefSchema(GroupSchema):

    class Meta:
        model = Group
        fields = ('id', 'name', '_links')
        ordered = True
        unknown = RAISE


class HostGroupMappingSchema(BaseSchema):

    class Meta:
        model = HostGroupMapping
        fields = ('id', 'host_id', 'group_id', 'priority', 'host', 'group',
                  'created_at', 'updated_at', '_links')
        ordered = True
        unknown = RAISE

    id = field_for(Host, 'id', dump_only=True)
    created_at = field_for(HostGroupMapping, 'created_at', dump_only=True)
    updated_at = field_for(HostGroupMapping, 'updated_at', dump_only=True)
    host = ma.Nested(  # pylint: disable=no-member
        'HostRefSchema', dump_only=True)
    group = ma.Nested(  # pylint: disable=no-member
        'GroupRefSchema', dump_only=True)

    _links = ma.Hyperlinks(
        {"self": ma.URLFor(
            "HostGroupMappingsAPI:get",
            host_id_or_name="<host_id>",
            host_group_mapping_id="<id>"),
         "collection": ma.URLFor(
            "HostGroupMappingsAPI:index",
            host_id_or_name="<host_id>")}
    )


class HostGroupMappingRefSchema(HostGroupMappingSchema):

    class Meta:
        model = HostGroupMapping
        fields = ('id', 'host_id', 'host_name', 'group_id', 'group_name',
                  'priority', '_links')
        ordered = True
        unknown = RAISE

    host_name = ma_fields.Pluck(
        'HostSchema', 'name', attribute='host', dump_only=True)
    group_name = ma_fields.Pluck(
        'GroupSchema', 'name', attribute='group', dump_only=True)
