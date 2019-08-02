from marshmallow import RAISE
from marshmallow import fields as ma_fields
from marshmallow_sqlalchemy import field_for
from opsy.inventory.models import Zone, Host, Group, HostGroupMapping
from opsy.flask_extensions import ma
from opsy.schema import BaseSchema, Hyperlinks

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

    id = field_for(Zone, 'id', dump_only=True,
                   description='The ID of the zone.')
    name = field_for(Zone, 'name', required=True,
                     description='The name of the zone.')
    vars = field_for(Zone, 'vars', field_class=ma_fields.Dict)
    created_at = field_for(Zone, 'created_at', dump_only=True)
    updated_at = field_for(Zone, 'updated_at', dump_only=True)
    _links = Hyperlinks(
        {"self": ma.URLFor("inventory_zones.zones_get", id_or_name="<id>"),
         "collection": ma.URLFor("inventory_zones.zones_list")},
        dump_only=True
    )


class ZoneQuerySchema(ZoneSchema):

    class Meta:
        model = Zone
        fields = ('id', 'name', 'description')
        ordered = True
        unknown = RAISE

    id = field_for(
        Zone, 'id',
        description='The unique UUID of the zone.')
    name = field_for(
        Zone, 'name', required=False,
        description='The unique name of the zone.')
    description = field_for(
        Zone, 'name', required=False,
        description='The description of the zone.')


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
                  'group_mappings', 'created_at', 'updated_at', '_links')
        ordered = True
        unknown = RAISE

    id = field_for(Host, 'id', dump_only=True)
    name = field_for(Host, 'name', required=True)
    zone_id = field_for(Host, 'zone_id', required=True)
    created_at = field_for(Host, 'created_at', dump_only=True)
    updated_at = field_for(Host, 'updated_at', dump_only=True)
    cpu_flags = field_for(Host, 'cpu_flags', field_class=ma_fields.Dict)
    disks = field_for(Host, 'disks', field_class=ma_fields.Dict)
    networking = field_for(Host, 'networking', field_class=ma_fields.Dict)
    vars = field_for(Host, 'vars', field_class=ma_fields.Dict)
    compiled_vars = ma_fields.Dict(dump_only=True)

    zone = ma.Nested(  # pylint: disable=no-member
        'ZoneRefSchema', dump_only=True)
    group_mappings = ma.Nested(  # pylint: disable=no-member
        'HostGroupMappingRefSchema', attribute='group_mappings',
        dump_only=True, many=True)

    _links = Hyperlinks(
        {"self": ma.URLFor("inventory_hosts.hosts_get", id_or_name="<id>"),
         "collection": ma.URLFor("inventory_hosts.hosts_list")},
        dump_only=True
    )


class HostQuerySchema(HostSchema):

    class Meta:
        model = Host
        fields = ('id', 'zone_id', 'zone_name', 'group_id', 'group_name',
                  'name', 'domain', 'manufacturer', 'model', 'cpu_arch',
                  'cpu_model', 'cpu_count', 'memory', 'swap', 'kernel', 'os',
                  'os_family', 'os_version', 'os_codename', 'os_arch',
                  'init_system')
        ordered = True
        unknown = RAISE

    id = field_for(Host, 'id')
    name = field_for(Host, 'name', required=False)
    zone_id = field_for(Host, 'zone_id', required=False)
    zone_name = ma_fields.String(attribute='zone___name')
    group_id = ma_fields.String(attribute='groups___id')
    group_name = ma_fields.String(attribute='groups___name')


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

    id = field_for(Group, 'id', dump_only=True)
    created_at = field_for(Group, 'created_at', dump_only=True)
    updated_at = field_for(Group, 'updated_at', dump_only=True)
    vars = field_for(Group, 'vars', field_class=ma_fields.Dict)
    compiled_vars = ma_fields.Dict(dump_only=True)
    zone = ma.Nested(  # pylint: disable=no-member
        'ZoneRefSchema', dump_only=True)
    parent = ma.Nested(  # pylint: disable=no-member
        'GroupRefSchema', dump_only=True)

    _links = Hyperlinks(
        {"self": ma.URLFor("inventory_groups.groups_get", id_or_name="<id>"),
         "collection": ma.URLFor("inventory_groups.groups_list")},
        dump_only=True
    )


class GroupQuerySchema(GroupSchema):

    class Meta:
        model = Group
        fields = ('id', 'name', 'zone_id', 'parent_id', 'parent_name',
                  'parent_name', 'host_id', 'host_name', 'default_priority')
        ordered = True
        unknown = RAISE

    id = field_for(Group, 'id')
    name = field_for(Group, 'name', required=False)
    zone_id = field_for(Group, 'zone_id', required=False)
    zone_name = ma_fields.String(attribute='zone___name')
    parent_name = ma_fields.String(attribute='parent___name')
    host_id = ma_fields.String(attribute='hosts___id')
    host_name = ma_fields.String(attribute='hosts___name')


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
    host_id = field_for(HostGroupMapping, 'id', dump_only=True)
    created_at = field_for(HostGroupMapping, 'created_at', dump_only=True)
    updated_at = field_for(HostGroupMapping, 'updated_at', dump_only=True)
    host = ma.Nested(  # pylint: disable=no-member
        'HostRefSchema', dump_only=True)
    group = ma.Nested(  # pylint: disable=no-member
        'GroupRefSchema', dump_only=True)

    _links = Hyperlinks({
        "self": ma.URLFor("inventory_hosts.host_group_mappings_get",
                          id_or_name="<host_id>", mapping_id="<id>"),
        "collection": ma.URLFor("inventory_hosts.host_group_mappings_list",
                                id_or_name="<host_id>")}, dump_only=True)


class HostGroupMappingQuerySchema(BaseSchema):

    class Meta:
        model = HostGroupMapping
        fields = ('id', 'group_id', 'group_name', 'priority')
        ordered = True
        unknown = RAISE

        group_name = ma_fields.String(attribute='group___name')


class HostGroupMappingRefSchema(HostGroupMappingSchema):

    class Meta:
        model = HostGroupMapping
        fields = ('id', 'host_id', 'host_name', 'group_id', 'group_name',
                  'priority', '_links')
        ordered = True
        unknown = RAISE