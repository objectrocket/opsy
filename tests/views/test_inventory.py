import json
from opsy.auth.utils import create_token
from opsy.inventory.models import Zone, Host, Group, HostGroupMapping

###############################################################################
# Zone Tests
###############################################################################


def test_zones_list(client, admin_user, test_user, test_inventory_bootstrap):
    # First we just create the token for both of our users.
    create_token(admin_user)
    create_token(test_user)
    # Then we use this token to list the zones for both users.
    admin_user_response = client.get(
        '/api/v1/zones/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    user_response = client.get(
        '/api/v1/zones/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    # Then we make sure we get the proper response codes.
    assert admin_user_response.status_code == 200
    assert user_response.status_code == 403
    # Now we parse the admin data.
    admin_response_data = json.loads(admin_user_response.data)
    # We should have 3 zones.
    assert len(admin_response_data) == 3
    # Let's test again with a filter.
    admin_user_response = client.get(
        '/api/v1/zones/?name=west',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    admin_response_data = json.loads(admin_user_response.data)
    # Now we should only have 1 zone named west.
    assert len(admin_response_data) == 1
    assert admin_response_data[0]['name'] == 'west'


def test_zones_post(client, admin_user, test_user, test_inventory_bootstrap):
    # Zone test data
    zone_data = {
        "name": "test zone",
        "description": "this is only a test",
        "vars": {}
    }
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test unprivileged user zone creation fails
    user_zone_create = client.post(
        '/api/v1/zones/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json=zone_data)
    assert user_zone_create.status_code == 403
    # Test admin user zone creation succeeds
    admin_zone_create = client.post(
        '/api/v1/zones/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=zone_data)
    assert admin_zone_create.status_code == 201
    # Verify admin user zone creation was successful
    admin_zone_verify = client.get(
        f"/api/v1/zones/{zone_data['name']}",
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    admin_zone_verify_data = json.loads(admin_zone_verify.data)
    assert admin_zone_verify_data['name'] == zone_data['name']
    # Verify duplicate zone insertion fails
    duplicate_insert = client.post(
        '/api/v1/zones/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=zone_data)
    assert duplicate_insert.status_code == 400


def test_zones_get(client, admin_user, test_user, test_inventory_bootstrap):
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test unprivileged user zone get by name fails
    user_zone_get_by_name = client.get(
        '/api/v1/zones/west',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert user_zone_get_by_name.status_code == 403
    # Test admin user zone get by name succeeds
    admin_zone_get_by_name = client.get(
        '/api/v1/zones/west',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_zone_get_by_name.status_code == 200
    admin_zone_get_by_name_data = json.loads(admin_zone_get_by_name.data)
    assert admin_zone_get_by_name_data['name'] == 'west'
    # Get a zone id to test
    zone_id = admin_zone_get_by_name_data['id']
    # Test unprivileged user get zone by id fails
    user_zone_get_by_id = client.get(
        f'/api/v1/zones/{zone_id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert user_zone_get_by_id.status_code == 403
    # Test admin user zone get by id succeeds
    admin_zone_get_by_id = client.get(
        f'/api/v1/zones/{zone_id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_zone_get_by_id.status_code == 200
    admin_zone_get_by_id_data = json.loads(admin_zone_get_by_id.data)
    assert admin_zone_get_by_id_data['name'] == 'west'
    # Test getting by name or id returns same data
    test_zone = Zone.get_by_id_or_name('west')
    zone_get_by_name = client.get(
        f'/api/v1/zones/{test_zone.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    zone_get_by_id = client.get(
        f'/api/v1/zones/{test_zone.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert zone_get_by_name.data == zone_get_by_id.data


def test_zones_patch(client, admin_user, test_user, test_inventory_bootstrap):
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test that patching nonexistent zone fails
    missing_zone_patch_by_name = client.patch(
        '/api/v1/zones/this_zone_should_not_exist',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json={"description": "nonexistent zone"})
    assert missing_zone_patch_by_name.status_code == 404
    missing_zone_patch_by_id = client.patch(
        'api/v1/zones/12345',  # that's the combination on my luggage!
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json={"description": "nonexistent zone"})
    assert missing_zone_patch_by_id.status_code == 404
    # Test that patching existing zone by admin succeeds
    zone_update_by_name = {"description": "updated by name"}
    zone_update_by_id = {"description": "updated by id"}
    # Patching by name
    admin_zone_patch_by_name = client.patch(
        '/api/v1/zones/west',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=zone_update_by_name)
    assert admin_zone_patch_by_name.status_code == 200
    get_updated_zone_by_name = client.get(
        '/api/v1/zones/west',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    get_updated_zone_by_name_data = json.loads(get_updated_zone_by_name.data)
    assert get_updated_zone_by_name_data['description'] == zone_update_by_name['description']
    # Patching by id
    zone_id = get_updated_zone_by_name_data['id']
    admin_zone_patch_by_id = client.patch(
        f'/api/v1/zones/{zone_id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=zone_update_by_id)
    assert admin_zone_patch_by_id.status_code == 200
    get_updated_zone_by_id = client.get(
        f'/api/v1/zones/{zone_id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    get_updated_zone_by_id_data = json.loads(get_updated_zone_by_id.data)
    assert get_updated_zone_by_id_data['description'] == zone_update_by_id['description']
    # Test that patching an existing zone by unprivileged user fails
    user_zone_patch_by_name = client.patch(
        '/api/v1/zones/west',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json={'description': 'updated'})
    assert user_zone_patch_by_name.status_code == 403
    user_zone_patch_by_id = client.patch(
        f'/api/v1/zones/{zone_id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json={'description': 'updated'})
    assert user_zone_patch_by_id.status_code == 403


def test_zones_delete(client, admin_user, test_user, test_inventory_bootstrap):
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test that deleting nonexistent zone fails
    delete_missing_name = client.delete(
        '/api/v1/zones/southbysouthwest',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert delete_missing_name.status_code == 404
    delete_missing_id = client.delete(
        '/api/v1/zones/12345',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert delete_missing_id.status_code == 404
    # Test that unprivileged user cannot delete zones
    delete_nopriv_name = client.delete(
        '/api/v1/zones/southbysouthwest',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert delete_nopriv_name.status_code == 403
    delete_nopriv_id = client.delete(
        '/api/v1/zones/12345',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert delete_nopriv_id.status_code == 403
    # Test that admin can delete zones
    delete_admin_name = client.delete(
        '/api/v1/zones/west',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert delete_admin_name.status_code == 204
    delete_admin_name_verify = client.get(
        '/api/v1/zones/west',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert delete_admin_name_verify.status_code == 404
    test_zone = Zone.get_by_id_or_name('east')
    delete_admin_id = client.delete(
        f'/api/v1/zones/{test_zone.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert delete_admin_id.status_code == 204
    delete_admin_id_verify = client.get(
        f'/api/v1/zones/{test_zone.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert delete_admin_id_verify == 404


###############################################################################
# Host Tests
###############################################################################

def test_hosts_list(client, admin_user, test_user, test_inventory_bootstrap):
    # Set up tokens
    create_token(admin_user)
    create_token(test_user)
    # Test that unprivileged user cannot list hosts
    list_hosts_nopriv = client.get(
        '/api/v1/hosts',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert list_hosts_nopriv.status_code == 403
    # Test that admin can list hosts
    list_hosts_admin = client.get(
        '/api/v1/hosts',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert list_hosts_admin.status_code == 200
    hosts_payload = json.loads(list_hosts_admin.data)
    assert len(hosts_payload) == 6
    # Test again with filter
    list_hosts_filter = client.get(
        '/api/v1/hosts/?name=westconsul',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert list_hosts_filter.status_code == 200
    list_hosts_filter_out = json.loads(list_hosts_filter.data)
    assert len(list_hosts_filter_out) == 1
    assert list_hosts_filter_out[0]['name'] == 'westconsul'


def test_hosts_post(client, admin_user, test_user, test_inventory_bootstrap):
    # Host test data
    test_host = {
        "zone_id": Zone.get_by_id_or_name('west').id,
        "name": "test host"
    }
    # Create tokens
    create_token(admin_user)
    create_token(test_user)
    # Test that a nopriv user cannot create a host
    host_create_nopriv = client.post(
        '/api/v1/hosts/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json=test_host)
    assert host_create_nopriv.status_code == 403
    # Test that admin can create a host
    host_create_admin = client.post(
        '/api/v1/hosts/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_host)
    assert host_create_admin.status_code == 201
    # Verify host was created correctly
    host_verify_admin = client.get(
        f"/api/v1/hosts/{test_host['name']}",
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    verify_out = json.loads(host_verify_admin.data)
    assert verify_out['name'] == test_host['name']
    # Test that creating a duplicate host fails
    host_dup_insert = client.post(
        '/api/v1/hosts/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_host)
    assert host_dup_insert.status_code == 400


def test_hosts_get(client, admin_user, test_user, test_inventory_bootstrap):
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Get a host for testing
    test_host = Host.get_by_id_or_name('westconsul')
    # Test that a nopriv user cannot get hosts
    host_nopriv_get_name = client.get(
        f'/api/v1/hosts/{test_host.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert host_nopriv_get_name.status_code == 403
    host_nopriv_get_id = client.get(
        f'/api/v1/hosts/{test_host.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert host_nopriv_get_id.status_code == 403
    # Test that admin can get hosts
    host_admin_get_name = client.get(
        f'/api/v1/hosts/{test_host.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert host_admin_get_name.status_code == 200
    name_out = json.loads(host_admin_get_name.data)
    assert name_out['id'] == test_host.id
    host_admin_get_id = client.get(
        f'/api/v1/hosts/{test_host.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert host_admin_get_id.status_code == 200
    id_out = json.loads(host_admin_get_id.data)
    assert id_out['name'] == test_host.name
    # Test that hosts_get by name or id fails on nonexistent host
    fail_get_id = client.get(
        '/api/v1/hosts/12345',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert fail_get_id.status_code == 404
    fail_get_name = client.get(
        '/api/v1/hosts/asdfhjkl',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert fail_get_name.status_code == 404


def test_hosts_patch(client, admin_user, test_user, test_inventory_bootstrap):
    # Test data
    test_data = {"vars": {"deadbeef": True}}
    test_host = Host.get_by_id_or_name('westconsul')
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test that patching a nonexistent host fails
    nohost_patch_name = client.patch(
        '/api/v1/hosts/this_host_should_not_exist',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_data)
    assert nohost_patch_name.status_code == 404
    nohost_patch_id = client.patch(
        '/api/v1/hosts/12345',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_data)
    assert nohost_patch_id.status_code == 404
    # Test that patching by nopriv user fails
    nopriv_host_name = client.patch(
        f'/api/v1/hosts/{test_host.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json=test_data)
    assert nopriv_host_name.status_code == 403
    nopriv_host_id = client.patch(
        f'/api/v1/hosts/{test_host.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json=test_data)
    assert nopriv_host_id.status_code == 403
    # Test that patching by admin succeeds
    admin_host_name = client.patch(
        f'/api/v1/hosts/{test_host.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_data)
    assert admin_host_name.status_code == 200
    admin_verify_name = client.get(
        f'/api/v1/hosts/{test_host.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    name_out = json.loads(admin_verify_name.data)
    assert name_out['vars'] == test_data['vars']
    admin_host_id = client.patch(
        f'/api/v1/hosts/{test_host.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json={"vars": {}})
    assert admin_host_id.status_code == 200
    admin_verify_id = client.get(
        f'/api/v1/hosts/{test_host.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    id_out = json.loads(admin_verify_id.data)
    assert id_out['vars'] == {}


def test_hosts_delete(client, admin_user, test_user, test_inventory_bootstrap):
    # Test data
    test_hosts = [Host.get_by_id_or_name('westconsul'),
                  Host.get_by_id_or_name('eastconsul')]
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test that deleting a nonexistent host fails
    nohost_delete_name = client.delete(
        '/api/v1/hosts/not_a_host',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert nohost_delete_name.status_code == 404
    nohost_delete_id = client.delete(
        '/api/v1/hosts/12345',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert nohost_delete_id.status_code == 404
    # Test that nopriv user cannot delete hosts
    nopriv_delete_name = client.delete(
        f'/api/v1/hosts/{test_hosts[0].name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_delete_name.status_code == 403
    nopriv_delete_id = client.delete(
        f'/api/v1/hosts/{test_hosts[0].id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_delete_id.status_code == 403
    # Test that admin can delete hosts by name
    admin_delete_name = client.delete(
        f'/api/v1/hosts/{test_hosts[0].name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_delete_name.status_code == 204
    verify_name = client.get(
        f'/api/v1/hosts/{test_hosts[0].name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert verify_name.status_code == 404
    # Test that admin can delete hosts by id
    admin_delete_id = client.delete(
        f'/api/v1/hosts/{test_hosts[1].id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_delete_id.status_code == 204
    verify_id = client.get(
        f'/api/v1/hosts/{test_hosts[1].id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert verify_id.status_code == 404


###############################################################################
# Host Group Mapping Tests
###############################################################################


def test_host_group_mappings_list(client, test_user, admin_user, test_inventory_bootstrap):
    # Test data
    test_host = Host.get_by_id_or_name('westprom')
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test that listing nonexistent host fails
    nohost_list_name = client.get(
        '/api/v1/hosts/not_a_host/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert nohost_list_name.status_code == 404
    nohost_list_id = client.get(
        '/api/v1/hosts/12345/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert nohost_list_id.status_code == 404
    # Test that listing by nopriv user fails
    nopriv_list_name = client.get(
        f'/api/v1/hosts/{test_host.name}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_list_name.status_code == 403
    nopriv_list_id = client.get(
        f'/api/v1/hosts/{test_host.id}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_list_id.status_code == 403
    # Test that listing by admin succeeds
    admin_list_name = client.get(
        f'/api/v1/hosts/{test_host.name}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_list_name.status_code == 200
    name_out = json.loads(admin_list_name.data)
    api_ids = sorted([x['id'] for x in name_out])
    host_ids = sorted([y.id for y in test_host.group_mappings])
    assert host_ids == api_ids
    # and by id
    admin_list_id = client.get(
        f'/api/v1/hosts/{test_host.id}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_list_id.status_code == 200
    id_out = sorted([z['id'] for z in json.loads(admin_list_id.data)])
    assert id_out == host_ids
    # Test again with a filter
    admin_filter = client.get(
        f'/api/v1/hosts/{test_host.name}/group_mappings/?id={test_host.group_mappings[0].id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_filter.status_code == 200
    admin_filter_out = json.loads(admin_filter.data)
    assert len(admin_filter_out) == 1
    assert admin_filter_out[0]['id'] == test_host.group_mappings[0].id


def test_host_group_mappings_post(client, test_user, admin_user, test_inventory_bootstrap):
    # Test data
    zone = Zone.get_by_id_or_name('west')
    test_group = Group.create(name='test group', zone=zone)
    test_host = Host.get_by_id_or_name('westprom')
    another_host = Host.get_by_id_or_name('westconsul')
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test that adding a group mapping to a nonexistent host fails
    nohost_mapping_name = client.post(
        '/api/v1/hosts/not_a_host/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json={"group_id": test_group.id})
    assert nohost_mapping_name.status_code == 404
    # by id as well
    nohost_mapping_id = client.post(
        '/api/v1/hosts/12345/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json={"group_id": test_group.id})
    assert nohost_mapping_id.status_code == 404
    # Test that mapping a nonexistent group to a host fails
    nogroup_mapping_name = client.post(
        f'/api/v1/hosts/{test_host.name}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json={"group_id": "12345"})
    assert nogroup_mapping_name.status_code == 404
    # also by id
    nogroup_mapping_id = client.post(
        f'/api/v1/hosts/{test_host.id}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json={"group_id": "12345"})
    assert nogroup_mapping_id.status_code == 404
    # Test that adding a group to a host by nopriv user fails
    nopriv_mapping_name = client.post(
        f'/api/v1/hosts/{test_host.name}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json={"group_id": test_group.id})
    assert nopriv_mapping_name.status_code == 403
    # nopriv by id
    nopriv_mapping_id = client.post(
        f'/api/v1/hosts/{test_host.id}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json={"group_id": test_group.id})
    assert nopriv_mapping_id.status_code == 403
    # Try it with an invalid group as well
    nopriv_mapping_nogroup = client.post(
        f'/api/v1/hosts/{test_host.name}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json={"group_id": "12345"})
    assert nopriv_mapping_nogroup.status_code == 403  # not 404
    # Test that admin can add a group mapping
    admin_mapping_name = client.post(
        f'/api/v1/hosts/{test_host.name}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json={"group_id": f"{test_group.id}"})
    assert admin_mapping_name.status_code == 201
    verify_name = client.get(
        f'/api/v1/hosts/{test_host.name}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    verify_name_list = [x['id'] for x in json.loads(verify_name.data)]
    mapping1 = HostGroupMapping.query.filter_by(
        group_id=test_group.id,
        host_id=test_host.id).first()
    assert mapping1.id in verify_name_list
    # Again, with id
    admin_mapping_id = client.post(
        f'/api/v1/hosts/{another_host.id}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json={"group_id": test_group.id})
    assert admin_mapping_id.status_code == 201
    verify_id = client.get(
        f'/api/v1/hosts/{another_host.id}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    verify_id_list = [y['id'] for y in json.loads(verify_id.data)]
    mapping2 = HostGroupMapping.query.filter_by(
        group_id=test_group.id,
        host_id=another_host.id).first()
    assert mapping2.id in verify_id_list
    # Test that adding a duplicate fails
    dup_mapping = client.post(
        f'/api/v1/hosts/{another_host.name}/group_mappings',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json={"group_id": test_group.id})
    assert dup_mapping.status_code == 400


def test_host_group_mappings_get(client, test_user, admin_user, test_inventory_bootstrap):
    # Test data
    test_host = Host.get_by_id_or_name('westprom')
    test_group = test_host.groups[0]
    test_mapping = HostGroupMapping.get_by_host_and_group(test_host.id, test_group.id)
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test that invalid host name fails with valid mapping
    nohost_get_name = client.get(
        f'/api/v1/hosts/not_a_host/group_mappings/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert nohost_get_name.status_code == 404
    # Test that invalid host id also fails with valid mapping
    nohost_get_id = client.get(
        f'/api/v1/hosts/12345/group_mappings/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert nohost_get_id.status_code == 404
    # by group name as well
    nohost_get_id_groupname = client.get(
        f'/api/v1/hosts/12345/group_mappings/{test_group.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert nohost_get_id_groupname.status_code == 404
    # Test that invalid host name with valid group name fails
    nohost_get_name_groupname = client.get(
        f'/api/v1/hosts/not_a_host/group_mappings/{test_group.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert nohost_get_name_groupname.status_code == 404
    # Test invalid host with invalid mapping
    nohost_get_nomap = client.get(
        f'/api/v1/hosts/not_a_host/group_mappings/12345',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert nohost_get_nomap.status_code == 404
    # By id as well
    nohost_get_nomap_id = client.get(
        f'/api/v1/hosts/98765/group_mappings/asdf',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert nohost_get_nomap_id.status_code == 404
    # Test that nopriv user cannot get mappings
    nopriv_get_name = client.get(
        f'/api/v1/hosts/{test_host.name}/group_mappings/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_get_name.status_code == 403
    # Test by id as well
    nopriv_get_id = client.get(
        f'/api/v1/hosts/{test_host.id}/group_mappings/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_get_id.status_code == 403
    # Test by group name as well
    gn_nopriv_get_name = client.get(
        f'/api/v1/hosts/{test_host.name}/group_mappings/{test_group.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert gn_nopriv_get_name.status_code == 403
    # Test nopriv by host id with group name
    gn_nopriv_get_id = client.get(
        f'/api/v1/hosts/{test_host.id}/group_mappings/{test_group.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert gn_nopriv_get_id.status_code == 403
    # Test that invalid host with nopriv user fails correctly
    nopriv_nohost = client.get(
        f'/api/v1/hosts/not_a_host/group_mappings/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_nohost.status_code == 403  # not 404
    # Test that invalid mapping with nopriv user fails correctly
    nopriv_nomap = client.get(
        f'/api/v1/hosts/{test_host.id}/group_mappings/12345',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_nomap.status_code == 403  # not 404
    # Test that admin can get mappings by host name
    admin_get_name = client.get(
        f'/api/v1/hosts/{test_host.name}/group_mappings/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_get_name.status_code == 200
    name_out = json.loads(admin_get_name.data)
    assert name_out['id'] == test_mapping.id
    # and by id
    admin_get_id = client.get(
        f'/api/v1/hosts/{test_host.id}/group_mappings/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_get_id.status_code == 200
    id_out = json.loads(admin_get_id.data)
    assert id_out['id'] == test_mapping.id
    # and by group name
    admin_get_group_name = client.get(
        f'/api/v1/hosts/{test_host.name}/group_mappings/{test_group.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_get_group_name.status_code == 200
    group_name_out = json.loads(admin_get_group_name.data)
    assert group_name_out['id'] == test_mapping.id
    # once more, with host id and group name
    admin_get_group_id = client.get(
        f'/api/v1/hosts/{test_host.id}/group_mappings/{test_group.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_get_group_id.status_code == 200
    group_id_out = json.loads(admin_get_group_id.data)
    assert group_id_out['id'] == test_mapping.id


def test_host_group_mappings_patch(client, test_user, admin_user, test_inventory_bootstrap):
    # Test data
    test_host = Host.get_by_id_or_name('westprom')
    test_group = test_host.groups[0]
    test_data = {"priority": 9}
    alt_data = {"priority": 8}
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test invalid data - invalid host id
    invalid_host_id = client.patch(
        f'/api/v1/hosts/12345/group_mappings/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_data)
    assert invalid_host_id.status_code == 404
    # Invalid host name
    invalid_host_name = client.patch(
        f'/api/v1/hosts/not_a_host/group_mappings/{test_group.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_data)
    assert invalid_host_name.status_code == 404
    # Invalid group id
    invalid_group_id = client.patch(
        f'/api/v1/hosts/{test_host.name}/group_mappings/12345',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_data)
    assert invalid_group_id.status_code == 404
    # Invalid group name
    invalid_group_name = client.patch(
        f'/api/v1/hosts/{test_host.id}/group_mappings/not_a_group',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_data)
    assert invalid_group_name.status_code == 404
    # Test nopriv user - host name, group name
    nopriv_name_name = client.patch(
        f'/api/v1/hosts/{test_host.name}/group_mappings/{test_group.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json=test_data)
    assert nopriv_name_name.status_code == 403
    # nopriv - host name, group id
    nopriv_name_id = client.patch(
        f'/api/v1/hosts/{test_host.name}/group_mappings/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json=test_data)
    assert nopriv_name_id.status_code == 403
    # nopriv - host id, group name
    nopriv_id_name = client.patch(
        f'/api/v1/hosts/{test_host.id}/group_mappings/{test_group.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json=test_data)
    assert nopriv_id_name.status_code == 403
    # nopriv - host id, group id
    nopriv_id_id = client.patch(
        f'/api/v1/hosts/{test_host.id}/group_mappings/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json=test_data)
    assert nopriv_id_id.status_code == 403
    # Test admin user - host name, group name
    admin_name_name = client.patch(
        f'/api/v1/hosts/{test_host.name}/group_mappings/{test_group.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_data)
    assert admin_name_name.status_code == 200
    output_name_name = json.loads(admin_name_name.data)
    assert output_name_name['priority'] == test_data['priority']
    # admin - host name, group id
    admin_name_id = client.patch(
        f'/api/v1/hosts/{test_host.name}/group_mappings/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=alt_data)
    assert admin_name_id.status_code == 200
    output_name_id = json.loads(admin_name_id.data)
    assert output_name_id['priority'] == alt_data['priority']
    # admin - host id, group name
    admin_id_name = client.patch(
        f'/api/v1/hosts/{test_host.id}/group_mappings/{test_group.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_data)
    assert admin_id_name.status_code == 200
    output_id_name = json.loads(admin_id_name.data)
    assert output_id_name['priority'] == test_data['priority']
    # admin - host id, group id
    admin_id_id = client.patch(
        f'/api/v1/hosts/{test_host.id}/group_mappings/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=alt_data)
    assert admin_id_id.status_code == 200
    output_id_id = json.loads(admin_id_id.data)
    assert output_id_id['priority'] == alt_data['priority']


def test_host_group_mappings_delete(client, test_user, admin_user, test_inventory_bootstrap):
    # Test all the data
    test_host1 = Host.get_by_id_or_name('westprom')
    test_group1 = test_host1.groups[0]
    test_group2 = test_host1.groups[1]
    test_mapping1 = HostGroupMapping.get_by_host_and_group(test_host1.id, test_group1.id)
    test_mapping2 = HostGroupMapping.get_by_host_and_group(test_host1.id, test_group2.id)
    test_host2 = Host.get_by_id_or_name('westconsul')
    test_group3 = test_host2.groups[0]
    test_mapping3 = HostGroupMapping.get_by_host_and_group(test_host2.id, test_group3.id)
    test_host3 = Host.get_by_id_or_name('eastprom')
    test_group4 = test_host3.groups[0]
    test_mapping4 = HostGroupMapping.get_by_host_and_group(test_host3.id, test_group4.id)
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test invalid data - host name, group name
    invalid_name_name = client.delete(
        '/api/v1/hosts/not_a_host/group_mappings/not_a_group',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert invalid_name_name.status_code == 404
    # Test invalid data - host name, group id
    invalid_name_id = client.delete(
        '/api/v1/hosts/not_a_host/group_mappings/12345',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert invalid_name_id.status_code == 404
    # Test invalid data - host id, group name
    invalid_id_name = client.delete(
        '/api/v1/hosts/12345/group_mappings/not_a_group',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert invalid_id_name.status_code == 404
    # Test invalid data - host id, group id
    invalid_id_id = client.delete(
        '/api/v1/hosts/12345/group_mappings/98765',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert invalid_id_id.status_code == 404
    # Test nopriv user - host name, group name
    nopriv_name_name = client.delete(
        f'/api/v1/hosts/{test_host1.name}/group_mappings/{test_group1.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_name_name.status_code == 403
    # Test nopriv user - host name, group id
    nopriv_name_id = client.delete(
        f'/api/v1/hosts/{test_host1.name}/group_mappings/{test_group1.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_name_id.status_code == 403
    # Test nopriv user - host id, group name
    nopriv_id_name = client.delete(
        f'/api/v1/hosts/{test_host1.id}/group_mappings/{test_group1.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_id_name.status_code == 403
    # Test nopriv user - host id, group id
    nopriv_id_id = client.delete(
        f'/api/v1/hosts/{test_host1.id}/group_mappings/{test_group1.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_id_id.status_code == 403
    # Test admin user - host name, group name
    admin_name_name = client.delete(
        f'/api/v1/hosts/{test_host1.name}/group_mappings/{test_group1.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_name_name.status_code == 204
    assert HostGroupMapping.query.filter_by(id=test_mapping1.id).first() is None
    # Test admin user - host name, group id
    admin_name_id = client.delete(
        f'/api/v1/hosts/{test_host1.name}/group_mappings/{test_group2.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_name_id.status_code == 204
    assert HostGroupMapping.query.filter_by(id=test_mapping2.id).first() is None
    # Test admin user - host id, group name
    admin_id_name = client.delete(
        f'/api/v1/hosts/{test_host2.id}/group_mappings/{test_group3.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_id_name.status_code == 204
    assert HostGroupMapping.query.filter_by(id=test_mapping3.id).first() is None
    # Test admin user - host id, group id
    admin_id_id = client.delete(
        f'/api/v1/hosts/{test_host3.id}/group_mappings/{test_group4.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_id_id.status_code == 204
    assert HostGroupMapping.query.filter_by(id=test_mapping4.id).first() is None


###############################################################################
# Group Tests
###############################################################################


def test_groups_list(client, test_user, admin_user, test_inventory_bootstrap):
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test that nopriv user cannot list groups
    nopriv_list = client.get(
        '/api/v1/groups/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_list.status_code == 403
    # Test that admin user can list groups
    admin_list = client.get(
        '/api/v1/groups/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_list.status_code == 200
    # there should be 5 groups
    assert len(json.loads(admin_list.data)) == 5
    # Test with a filter as well
    admin_filter = client.get(
        '/api/v1/groups/?name=default',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_filter.status_code == 200
    assert len(json.loads(admin_filter.data)) == 1


def test_groups_post(client, test_user, admin_user, test_inventory_bootstrap):
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test that nopriv user cannot create a group
    nopriv_post = client.post(
        '/api/v1/groups/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json={"name": "test group"})
    assert nopriv_post.status_code == 403
    # Test that admin user can create a group
    admin_post = client.post(
        '/api/v1/groups/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json={"name": "test group", "vars": {"test": 9001}})
    assert admin_post.status_code == 201
    # Verify group created successfully
    verify_post = json.loads(admin_post.data)
    verify_group = Group.get_by_id(verify_post['id'])
    assert verify_post['vars'] == verify_group.vars
    # Test that creating a duplicate group fails
    dup_post = client.post(
        '/api/v1/groups/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json={"name": "test group", "vars": {"different_var": 1138}})
    assert dup_post.status_code == 400


def test_groups_get(client, test_user, admin_user, test_inventory_bootstrap):
    # Test data
    test_group = Host.get_by_id_or_name('westprom').groups[0]
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test that nopriv user cannot get a group
    nopriv_get = client.get(
        f'/api/v1/groups/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_get.status_code == 403
    # Test that getting an invalid group fails
    invalid_get = client.get(
        '/api/v1/groups/12345',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert invalid_get.status_code == 404
    # Test that admin can get a group
    admin_get = client.get(
        f'/api/v1/groups/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_get.status_code == 200
    admin_get_out = json.loads(admin_get.data)
    assert admin_get_out['name'] == test_group.name


def test_groups_patch(client, test_user, admin_user, test_inventory_bootstrap):
    # Test data
    test_group = Host.get_by_id_or_name('westprom').groups[0]
    test_data = {"vars": {"test": 1}}
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test that nopriv user cannot patch a group
    nopriv_patch = client.patch(
        f'/api/v1/groups/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)],
        json=test_data)
    assert nopriv_patch.status_code == 403
    # Test that patcing invalid group fails
    invalid_patch = client.patch(
        '/api/v1/groups/12345',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_data)
    assert invalid_patch.status_code == 404
    # Test that admin can patch a group
    admin_patch = client.patch(
        f'/api/v1/groups/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)],
        json=test_data)
    assert admin_patch.status_code == 200
    admin_patch_out = json.loads(admin_patch.data)
    assert admin_patch_out['vars'] == test_data['vars']


def test_groups_delete(client, test_user, admin_user, test_inventory_bootstrap):
    # Test data
    test_group = Host.get_by_id_or_name('westprom').groups[0]
    # Create tokens
    create_token(test_user)
    create_token(admin_user)
    # Test that nopriv user cannot delete a group
    nopriv_delete = client.delete(
        f'/api/v1/groups/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user.session_token)])
    assert nopriv_delete.status_code == 403
    # Test that deleting an invalid group fails
    invalid_delete = client.delete(
        '/api/v1/groups/12345',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert invalid_delete.status_code == 404
    # Test that admin can delete a group
    admin_delete = client.delete(
        f'/api/v1/groups/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert admin_delete.status_code == 204
    verify = client.get(
        f'/api/v1/groups/{test_group.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', admin_user.session_token)])
    assert verify.status_code == 404
