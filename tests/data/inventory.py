from faker import Faker
from opsy.inventory.models import Zone, Group, Host


def test_zone():
    try:
        return Zone.get_by_id_or_name('test')
    except ValueError:
        return Zone.create(name='test')


def test_zones(number=10):
    fake = Faker(locale='en_US')
    fake.seed(8675309)
    zones = []
    for x in range(0, number):
        zones.append(Zone.create(name=fake.domain_word()))
    return zones


def test_group():
    return Group.create(name='test')


def test_groups(number=10):
    fake = Faker(locale='en_US')
    fake.seed(8675309)
    groups = []
    for x in range(0, number):
        groups.append(Group.create(name=fake.domain_word()))
    return groups


def test_host():
    try:
        zone = Zone.get_by_id_or_name('test')
    except ValueError:
        zone = Zone.create(name='test')
    return Host.create(name='test', zone_id=zone.id)


def test_hosts(number=10):
    fake = Faker(locale='en_US')
    fake.seed(8675309)
    try:
        zone = Zone.get_by_id_or_name('test')
    except ValueError:
        zone = Zone.create(name='test')
    hosts = []
    for x in range(0, number):
        hosts.append(Host.create(name=fake.domain_word(), zone_id=zone.id))
    return hosts


def test_inventory_bootstrap():
    """Just populates the DB with some inventory assets for testing."""
    west_zone = Zone.create(
        name='west', vars={'datacenter': 'west', 'prom_node': 'westprom'})
    central_zone = Zone.create(
        name='central', vars={'datacenter': 'central', 'prom_node': 'centralprom'})
    east_zone = Zone.create(
        name='east', vars={'datacenter': 'east', 'prom_node': 'eastprom'})
    west_default = Group.create(
        name='default', zone=west_zone,
        vars={'shutup': 'meg', 'default': True})
    global_prom = Group.create(name='prom_nodes', vars={'thanos': True})
    west_prom = Group.create(
        name='prom_nodes', zone=west_zone, parent=global_prom,
        vars={'prom_region': 'west', 'shutup': 'sam'})
    central_prom = Group.create(
        name='prom_nodes', zone=central_zone, parent=global_prom,
        vars={'prom_region': 'central', 'thanos': False})
    east_prom = Group.create(
        name='prom_nodes', zone=east_zone, parent=global_prom,
        vars={'prom_region': 'east'})
    for group in [west_prom, central_prom, east_prom]:
        consul = Host.create(
            name=f'{group.zone.name}consul', zone=group.zone)
        prom = Host.create(
            name=f'{group.zone.name}prom', zone=group.zone,
            vars={'consul_node': consul.name})
        prom.add_group(group)
        if group.zone.name == 'west':
            prom.add_group(west_default)
            consul.add_group(west_default)
    return True
