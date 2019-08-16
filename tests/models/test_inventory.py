import pytest
from opsy.inventory.models import Host, Group, Zone, HostGroupMapping
from opsy.exceptions import DuplicateError


def test_zone_model(test_inventory_bootstrap):
    """Test Zone to make sure it works correctly."""
    # Test to make sure deleting a zone nukes all assets in that zone
    west_zone = Zone.query.filter_by(name='west').first()
    west_prom_nodes_group_id = Group.query.filter_by(
        name='prom_nodes', zone_id=west_zone.id).first().id
    westprom_id = Host.query.filter_by(
        name='westprom', zone_id=west_zone.id).first().id
    westconsul_id = Host.query.filter_by(
        name='westconsul', zone_id=west_zone.id).first().id
    westprom_group_mapping_id = HostGroupMapping.query.filter_by(
        host_id=westprom_id, group_id=west_prom_nodes_group_id).first().id
    west_zone.delete()
    assert Group.query.filter_by(
        id=west_prom_nodes_group_id).first() is None
    assert Host.query.filter_by(id=westprom_id).first() is None
    assert Host.query.filter_by(id=westconsul_id).first() is None
    assert HostGroupMapping.query.filter_by(
        id=westprom_group_mapping_id).first() is None
    # Make sure the rest of the stuff is still there
    assert len(Zone.query.all()) == 2  # east and central
    assert len(Group.query.all()) == 3  # 1 global group, and 1 per zone
    assert len(Host.query.all()) == 4  # 2 hosts per zone
    assert len(HostGroupMapping.query.all()) == 2  # 1 mapping per zone


def test_host_model(test_host, test_group, test_inventory_bootstrap):
    """Test Host to make sure it works correctly."""
    # {'datacenter': 'west', 'prom_node': 'westprom'}
    west_zone = Zone.query.filter_by(name='west').first()
    east_zone = Zone.query.filter_by(name='east').first()
    prom_group = Group.query.filter_by(
        name='prom_nodes', zone_id=None).first()
    west_prom_group = Group.query.filter_by(
        name='prom_nodes', zone_id=west_zone.id).first()
    east_prom_group = Group.query.filter_by(
        name='prom_nodes', zone_id=east_zone.id).first()
    west_default_group = Group.query.filter_by(
        name='default', zone_id=west_zone.id).first()
    west_default_group = Group.query.filter_by(
        name='default', zone_id=west_zone.id).first()
    test_host.update(zone_id=west_zone.id)
    # Test __repr__
    assert test_host.__repr__() == (
        f'<{test_host.__class__.__name__} {test_host.zone.name}/'
        f'{test_host.name}>')
    # Test that compiled_vars should only be the zone vars at the moment
    assert test_host.compiled_vars == west_zone.vars
    # Now add vars and make sure they merge
    test_host.update(vars={'test': True})
    assert test_host.compiled_vars == {'datacenter': 'west',
                                       'prom_node': 'westprom',
                                       'test': True}
    # Test adding a group
    # Make sure it yells at us if we're not in a zone
    with pytest.raises(ValueError):
        test_host.add_group(test_group)
    # Make sure it yells at us if we're in a different zone
    test_group.update(zone_id=east_zone.id)
    with pytest.raises(ValueError):
        test_host.add_group(test_group)
    # Okay, let's actually add it now and make sure it looks right
    test_group.update(zone_id=test_host.zone.id)
    test_host.add_group(test_group)
    test_group_mapping = HostGroupMapping.query.filter_by(
        host_id=test_host.id, group_id=test_group.id).first()
    assert test_group_mapping is not None
    assert isinstance(test_group_mapping, HostGroupMapping)
    assert test_group_mapping in test_host.group_mappings
    assert test_group_mapping in test_group.host_mappings
    assert test_group_mapping.host_name == test_host.name
    assert test_group_mapping.group_name == test_group.name
    assert test_group_mapping.priority == 100
    assert test_host.get_group_priority(test_group) == 100
    # Let's also test HostGroupMapping.get_by_host_and_group works
    assert HostGroupMapping.get_by_host_and_group(
        test_host.id, test_group.id) == test_group_mapping
    assert HostGroupMapping.get_by_host_and_group(
        test_host.name, test_group.name) == test_group_mapping
    # And make sure it yells at us if we give it nonsense
    with pytest.raises(ValueError):
        HostGroupMapping.get_by_host_and_group('notarealhost', 'notarealgroup')
    # Make sure we can't change the group's zone after we've added a host
    with pytest.raises(ValueError):
        test_group.update(zone_id=None)
    # Make sure it yells at us if we try adding it again
    with pytest.raises(DuplicateError):
        test_host.add_group(test_group)
    # Test that adding vars to the group properly overides zone vars
    test_group.update(vars={'prom_node': 'truewestprom', 'shutup': 'sam'})
    assert test_host.compiled_vars == {'datacenter': 'west',
                                       'prom_node': 'truewestprom',
                                       'test': True,
                                       'shutup': 'sam'}
    # Let's add another group with a higher priority
    test_host.add_group(west_default_group, priority=110)
    west_default_group_mapping = HostGroupMapping.query.filter_by(
        host_id=test_host.id, group_id=west_default_group.id).first()
    assert west_default_group_mapping.priority == 110
    assert test_host.get_group_priority(west_default_group) == 110
    # Make sure it orders correctly (lower priority == lower index)
    assert test_host.groups == [test_group, west_default_group]
    assert test_host.group_mappings == [test_group_mapping,
                                        west_default_group_mapping]
    # Let's make sure those vars also show up
    assert test_host.compiled_vars == {'datacenter': 'west',
                                       'prom_node': 'truewestprom',
                                       'test': True,
                                       'shutup': 'meg',
                                       'default': True}
    # Let's change the priority and check again
    test_host.change_group_priority(west_default_group, 90)
    assert west_default_group_mapping.priority == 90
    assert test_host.get_group_priority(west_default_group) == 90
    assert test_host.groups == [west_default_group, test_group]
    assert test_host.group_mappings == [west_default_group_mapping,
                                        test_group_mapping]
    assert test_host.compiled_vars == {'datacenter': 'west',
                                       'prom_node': 'truewestprom',
                                       'test': True,
                                       'shutup': 'sam',
                                       'default': True}
    # Let's add a parent group in the same zone and check that the variables
    # get applied
    west_default_group.update(parent_id=west_prom_group.id)
    assert test_host.compiled_vars == {'datacenter': 'west',
                                       'prom_node': 'truewestprom',
                                       'prom_region': 'west',
                                       'test': True,
                                       'shutup': 'sam',
                                       'default': True}
    # Now a parent with no zone
    west_default_group.update(parent_id=prom_group.id)
    assert test_host.compiled_vars == {'datacenter': 'west',
                                       'prom_node': 'truewestprom',
                                       'thanos': True,
                                       'test': True,
                                       'shutup': 'sam',
                                       'default': True}
    # Now let's make sure it yells at us if we try to change the parent to a
    # group in a different zone
    with pytest.raises(ValueError):
        west_default_group.update(parent_id=east_prom_group.id)
    # Now let's remove the group
    test_host.remove_group(west_default_group)
    assert HostGroupMapping.query.filter_by(
        host_id=test_host.id, group_id=west_default_group.id).first() is None
    assert west_default_group not in test_host.groups
    assert test_host.compiled_vars == {'datacenter': 'west',
                                       'prom_node': 'truewestprom',
                                       'test': True,
                                       'shutup': 'sam'}
    # And make sure it yells at us if we try to remove it again
    with pytest.raises(ValueError):
        test_host.remove_group(west_default_group)
    # Or check the priority
    with pytest.raises(ValueError):
        test_host.get_group_priority(west_default_group)
    # Or change the priority
    with pytest.raises(ValueError):
        test_host.change_group_priority(west_default_group, 100)


def test_group_model(test_host, test_group, test_inventory_bootstrap):
    """Test Group to make sure it works correctly.

    We already tested just about all the methods through the Host tests
    since the Host methods just call the Group methods for manipulating
    group mappings."""

    # Test __repr__ without zone
    assert test_group.__repr__() == (
        f'<{test_group.__class__.__name__} None/{test_group.name}>')
    test_group.update(zone_id=test_host.zone.id)
    # Test __repr__ with zone
    assert test_group.__repr__() == (
        f'<{test_group.__class__.__name__} {test_group.zone.name}/'
        f'{test_group.name}>')
    # This should work
    Group.create('my_very_own_new_group')
    # This should throw a DuplicateError
    with pytest.raises(DuplicateError):
        Group.create('my_very_own_new_group')
    # But this should work
    zone = Zone.create('my_very_own_new_zone')
    Group.create('my_very_own_new_group', zone=zone)
