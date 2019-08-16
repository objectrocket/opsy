import pytest
import datetime as dt
from opsy.auth.models import User
from opsy.inventory.models import Host, Group

###############################################################################
# OpsyQuery
###############################################################################


def test_opsy_query(test_user, test_users, test_inventory_bootstrap):
    """Test opsy_query to make sure it works correctly."""
    # Test get_or_fail
    assert User.query.get_or_fail(test_user.id) == test_user
    with pytest.raises(ValueError):
        User.query.get_or_fail('thisisnotarealuser')
    # Test first_or_fail
    assert User.query.filter_by(id=test_user.id).first_or_fail() == test_user
    with pytest.raises(ValueError):
        User.query.filter_by(id='thisisnotarealuser').first_or_fail()
    # Setup for filter_in tests
    westprom = Host.query.filter_by(name='westprom').first()
    westconsul = Host.query.filter_by(name='westconsul').first()
    centralprom = Host.query.filter_by(name='centralprom').first()
    centralconsul = Host.query.filter_by(name='centralconsul').first()
    eastprom = Host.query.filter_by(name='eastprom').first()
    eastconsul = Host.query.filter_by(name='eastconsul').first()
    # Test empty query
    assert len(Host.query.filter_in().all()) == 6
    # Test if we don't give it a string it bypasses the string operations
    eastconsul.update(updated_at=dt.datetime.utcnow())
    assert Host.query.filter_in(
        updated_at=eastconsul.updated_at).first() == eastconsul
    # Test filter_in include
    assert Host.query.filter_in(name='westprom').first() == westprom
    for node in Host.query.filter_in(name='westprom,eastprom').all():
        assert node in [westprom, eastprom]
    # Test filter_in exclude
    assert len(Host.query.filter_in(name='!westprom').all()) == 5
    for node in Host.query.filter_in(name='!westprom').all():
        assert isinstance(node, Host)
        assert node != westprom
        assert len(Host.query.filter_in(name='!westprom,!eastprom').all()) == 4
    for node in Host.query.filter_in(name='!westprom,!eastprom').all():
        assert isinstance(node, Host)
        assert node not in [westprom, eastprom]
    # Test filter_in like
    assert len(Host.query.filter_in(name='*prom').all()) == 3
    for node in Host.query.filter_in(name='*prom').all():
        assert isinstance(node, Host)
        assert node in [westprom, centralprom, eastprom]
    # Test filter_in not like
    assert len(Host.query.filter_in(name='!*prom').all()) == 3
    for node in Host.query.filter_in(name='!*prom').all():
        assert isinstance(node, Host)
        assert node not in [westprom, centralprom, eastprom]
    # Now all of these over again but with relationship filters!
    # We do these with both groups___name and zone___name since they're
    # different types of relationships (many-to-many and one-to-many).
    # Test filter_in include
    assert len(Host.query.filter_in(zone___name='east,west').all()) == 4
    for node in Host.query.filter_in(zone___name='east,west').all():
        assert isinstance(node, Host)
        assert node in [westprom, westconsul, eastprom, eastconsul]
    assert len(Host.query.filter_in(groups___name='prom_nodes').all()) == 3
    for node in Host.query.filter_in(groups___name='prom_nodes').all():
        assert isinstance(node, Host)
        assert node in [westprom, centralprom, eastprom]
    # Test filter_in exclude
    assert len(Host.query.filter_in(zone___name='!west,!east').all()) == 2
    for node in Host.query.filter_in(zone___name='!west,!east').all():
        assert isinstance(node, Host)
        assert node in [centralprom, centralconsul]
    assert len(Host.query.filter_in(groups___name='!prom_nodes').all()) == 3
    for node in Host.query.filter_in(groups___name='!prom_nodes').all():
        assert isinstance(node, Host)
        assert node in [westconsul, centralconsul, eastconsul]
    # Test filter_in like
    assert len(Host.query.filter_in(zone___name='*st').all()) == 4
    for node in Host.query.filter_in(zone___name='*st').all():
        assert isinstance(node, Host)
        assert node in [westprom, westconsul, eastprom, eastconsul]
    assert len(Host.query.filter_in(groups___name='prom*').all()) == 3
    for node in Host.query.filter_in(groups___name='prom*').all():
        assert isinstance(node, Host)
        assert node in [westprom, centralprom, eastprom]
    # Test filter_in not like
    assert len(Host.query.filter_in(zone___name='!*st').all()) == 2
    for node in Host.query.filter_in(zone___name='!*st').all():
        assert isinstance(node, Host)
        assert node in [centralprom, centralconsul]
    assert len(Host.query.filter_in(groups___name='!prom*').all()) == 3
    for node in Host.query.filter_in(groups___name='!prom*').all():
        assert isinstance(node, Host)
        assert node not in [westprom, centralprom, eastprom]


###############################################################################
# BaseModel
###############################################################################


def test_base_model(test_group, test_groups):
    """Test BaseModel to make sure it works correctly."""
    # Test __repr__ (have to use super here since Group overrides this)
    assert super(Group, test_group).__repr__() == \
        f'<{test_group.__class__.__name__} {test_group.id}>'
    # Test create
    new_group = Group.create(name='new_group')
    assert new_group.id is not None
    assert Group.query.filter_by(id=new_group.id).first() == new_group
    # Test update
    new_group.update(name='my_new_group')
    assert new_group.name == 'my_new_group'
    # Test Delete
    new_group_id = new_group.id
    new_group.delete()
    assert Group.query.filter_by(id=new_group_id).first() is None
    # Test get_by_id
    assert Group.get_by_id(test_group.id) == test_group
    with pytest.raises(ValueError):
        Group.get_by_id('thisgroupdoesntexist')
    # Test updated_by_id
    Group.update_by_id(test_group.id, name='my_test_group')
    assert test_group.name == 'my_test_group'
    with pytest.raises(ValueError):
        Group.update_by_id('thisgroupdoesntexist', name='Cool bois')
    # Test delete_by_id
    test_group_id = test_group.id
    Group.delete_by_id(test_group.id)
    assert Group.query.filter_by(id=test_group_id).first() is None
    with pytest.raises(ValueError):
        Group.delete_by_id('thisgroupdoesntexist')


###############################################################################
# NamedModel
###############################################################################


def test_named_model(test_user, test_users):
    """Test NamedModel to make sure it works correctly."""
    # Test __repr__
    assert test_user.__repr__() == \
        f'<{test_user.__class__.__name__} {test_user.name}>'
    # Test create
    new_user = User.create('new_user')
    assert new_user.id is not None
    assert User.query.filter_by(id=new_user.id).first() == new_user
    # Test get_by_id_or_name
    assert User.get_by_id_or_name(new_user.id) == new_user
    assert User.get_by_id_or_name(new_user.name) == new_user
    with pytest.raises(ValueError):
        User.get_by_id_or_name('thisuserdoesntexist')
    # Test update_by_id_or_name
    User.update_by_id_or_name(new_user.name, full_name='Bobby Tables')
    assert new_user.full_name == 'Bobby Tables'
    User.update_by_id_or_name(new_user.id, full_name='Little Bobby Tables')
    assert new_user.full_name == 'Little Bobby Tables'
    with pytest.raises(ValueError):
        User.update_by_id_or_name('thisuserdoesntexist', full_name='Hat Man')
    # Test delete_by_id_or_name
    new_user_id = new_user.id
    test_user_id = test_user.id
    User.delete_by_id_or_name(new_user.id)
    assert User.query.filter_by(id=new_user_id).first() is None
    User.delete_by_id_or_name(test_user.name)
    assert User.query.filter_by(id=test_user_id).first() is None
    with pytest.raises(ValueError):
        User.delete_by_id_or_name('thisuserdoesntexist')
