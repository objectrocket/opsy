from collections import OrderedDict
from opsy.inventory.schema import (
    ZoneSchema, ZoneQuerySchema, ZoneRefSchema,
    HostSchema, HostQuerySchema, HostRefSchema,
    GroupSchema, GroupQuerySchema, GroupRefSchema,
    HostGroupMappingSchema, HostGroupMappingQuerySchema,
    HostGroupMappingRefSchema)
from opsy.inventory.models import HostGroupMapping


###############################################################################
# ZoneSchema Tests
###############################################################################


def test_zone_schema(test_zone, test_zones):

    expected_zone_schema_output = OrderedDict([
        ('id', test_zone.id),
        ('name', test_zone.name),
        ('description', test_zone.description),
        ('vars', test_zone.vars),
        ('created_at', test_zone.created_at.isoformat()),
        ('updated_at', test_zone.updated_at.isoformat()),
        ('_links', {
            'self': f'/api/v1/zones/{test_zone.id}',
            'collection': '/api/v1/zones/'})])

    expected_zone_schema_input = OrderedDict([
        ('name', 'mytestzone')])

    expected_zone_ref_schema_output = OrderedDict([
        ('id', test_zone.id),
        ('name', test_zone.name),
        ('_links', {
            'self': f'/api/v1/zones/{test_zone.id}',
            'collection': '/api/v1/zones/'})])

    expected_zone_query_schema_output = OrderedDict([
        ('name', 'mytestzone')])

    assert ZoneSchema().dump(test_zone) == expected_zone_schema_output
    assert ZoneSchema().load(
        {'name': 'mytestzone'}) == expected_zone_schema_input
    assert ZoneRefSchema().dump(test_zone) == expected_zone_ref_schema_output
    assert ZoneQuerySchema(partial=True).dump(
        {'name': 'mytestzone'}) == expected_zone_query_schema_output


###############################################################################
# HostSchema Tests
###############################################################################


def test_host_schema(test_host, test_hosts):

    expected_host_schema_output = OrderedDict([
        ('id', test_host.id),
        ('zone_id', test_host.zone_id),
        ('name', test_host.name),
        ('vars', None),
        ('compiled_vars', {}),
        ('zone', OrderedDict([
            ('id', test_host.zone.id),
            ('name', test_host.zone.name),
            ('_links', {'self': f'/api/v1/zones/{test_host.zone_id}',
                        'collection': '/api/v1/zones/'})])),
        ('group_mappings', []),
        ('created_at', test_host.created_at.isoformat()),
        ('updated_at', test_host.updated_at.isoformat()),
        ('_links',
            {'self': f'/api/v1/hosts/{test_host.id}',
             'collection': '/api/v1/hosts/'})])

    expected_host_schema_input = OrderedDict([
        ('zone_id', test_host.zone_id),
        ('name', 'mytesthost')])

    expected_host_ref_schema_output = OrderedDict([
        ('id', test_host.id),
        ('name', test_host.name),
        ('_links', {
            'self': f'/api/v1/hosts/{test_host.id}',
            'collection': '/api/v1/hosts/'})])

    expected_host_query_schema_output = OrderedDict([
        ('name', 'mytesthost')])

    assert HostSchema().dump(test_host) == expected_host_schema_output
    assert HostSchema().load(
        {'name': 'mytesthost',
         'zone_id': test_host.zone_id}) == expected_host_schema_input
    assert HostRefSchema().dump(test_host) == expected_host_ref_schema_output
    assert HostQuerySchema(partial=True).dump(
        {'name': 'mytesthost'}) == expected_host_query_schema_output


###############################################################################
# GroupSchema Tests
###############################################################################


def test_group_schema(test_group, test_groups):

    expected_group_schema_output = OrderedDict([
        ('id', test_group.id),
        ('zone_id', test_group.zone_id),
        ('parent_id', test_group.parent_id),
        ('name', test_group.name),
        ('default_priority', test_group.default_priority),
        ('vars', test_group.vars),
        ('compiled_vars', test_group.compiled_vars),
        ('created_at', test_group.created_at.isoformat()),
        ('updated_at', test_group.updated_at.isoformat()),
        ('_links',
            {'self': f'/api/v1/groups/{test_group.id}',
             'collection': '/api/v1/groups/'})])

    expected_group_schema_input = OrderedDict([
        ('name', 'mytestgroup')])

    expected_group_ref_schema_output = OrderedDict([
        ('id', test_group.id),
        ('name', test_group.name),
        ('_links', {
            'self': f'/api/v1/groups/{test_group.id}',
            'collection': '/api/v1/groups/'})])

    expected_group_query_schema_output = OrderedDict([
        ('name', 'mytestgroup')])

    assert GroupSchema().dump(test_group) == expected_group_schema_output
    assert GroupSchema().load(
        {'name': 'mytestgroup'}) == expected_group_schema_input
    assert GroupRefSchema().dump(test_group) == expected_group_ref_schema_output
    assert GroupQuerySchema(partial=True).dump(
        {'name': 'mytestgroup'}) == expected_group_query_schema_output


###############################################################################
# HostGroupMappingSchema Tests
###############################################################################


def test_host_group_mapping_schema(test_inventory_bootstrap):

    test_mapping = HostGroupMapping.get_by_host_and_group(
        'westprom', 'prom_nodes')

    expected_host_group_mapping_schema_output = OrderedDict([
        ('id', test_mapping.id),
        ('host_id', test_mapping.host_id),
        ('group_id', test_mapping.group_id),
        ('priority', test_mapping.priority),
        ('host', OrderedDict([
            ('id', test_mapping.host.id),
            ('name', test_mapping.host.name),
            ('_links',
                {'self': f'/api/v1/hosts/{test_mapping.host.id}',
                 'collection': '/api/v1/hosts/'})])),
        ('group', OrderedDict([
            ('id', test_mapping.group.id),
            ('name', test_mapping.group.name),
            ('_links',
                {'self': f'/api/v1/groups/{test_mapping.group.id}',
                 'collection': '/api/v1/groups/'})])),
        ('created_at', test_mapping.created_at.isoformat()),
        ('updated_at', test_mapping.updated_at.isoformat()),
        ('_links',
            {'self': f'/api/v1/hosts/{test_mapping.host.id}'
                f'/group_mappings/{test_mapping.group.id}',
             'collection': f'/api/v1/hosts/{test_mapping.host.id}'
                '/group_mappings/'})])

    expected_host_group_mapping_ref_schema_output = OrderedDict([
        ('id', test_mapping.id),
        ('host_id', test_mapping.host_id),
        ('host_name', test_mapping.host_name),
        ('group_id', test_mapping.group_id),
        ('group_name', test_mapping.group_name),
        ('priority', test_mapping.priority),
        ('_links',
            {'self': f'/api/v1/hosts/{test_mapping.host.id}'
                f'/group_mappings/{test_mapping.group.id}',
             'collection': f'/api/v1/hosts/{test_mapping.host.id}'
                '/group_mappings/'})])

    expected_host_group_mapping_query_schema_output = OrderedDict([
        ('group_name', 'mytestmapping')])

    assert HostGroupMappingSchema().dump(test_mapping) == \
        expected_host_group_mapping_schema_output
    assert HostGroupMappingRefSchema().dump(test_mapping) == \
        expected_host_group_mapping_ref_schema_output
    assert HostGroupMappingQuerySchema().dump(
        {'group___name': 'mytestmapping'}) == \
        expected_host_group_mapping_query_schema_output
