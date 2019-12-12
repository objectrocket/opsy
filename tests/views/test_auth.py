import json
import pytest
from time import sleep
from opsy.auth.models import User, Role, Permission
from opsy.auth.schema import UserTokenSchema

###############################################################################
# Login Tests
###############################################################################


def test_login_get(client, test_user):
    """Functional test for login_get."""
    # First lets get our token
    test_user_token = test_user.get_id()
    # Let's make sure it yells at us if we don't give it a token
    response = client.get(
        '/api/v1/login/',
        follow_redirects=True)
    assert response.status_code == 403
    # Now let's make sure it gives us our token if we do have a token
    response = client.get(
        '/api/v1/login/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    # Then we make sure we get the proper response codes.
    assert response.status_code == 200
    assert json.loads(response.data) == UserTokenSchema().dump(test_user)


def test_login_post(client, test_user, disabled_user):
    """Functional test for login_post."""
    test_user_id = test_user.id
    disabled_user_id = disabled_user.id
    # Let's try to give it a non-existant user
    response = client.post(
        '/api/v1/login/',
        follow_redirects=True,
        json={'user_name': 'notrealboy', 'password': 'hopeless'})
    assert response.status_code == 401
    # Now let's try a wrong password
    response = client.post(
        '/api/v1/login/',
        follow_redirects=True,
        json={'user_name': 'test', 'password': 'hopeless'})
    assert response.status_code == 401
    # Now no password
    response = client.post(
        '/api/v1/login/',
        follow_redirects=True,
        json={'user_name': 'test'})
    assert response.status_code == 422
    # Now no user_name
    response = client.post(
        '/api/v1/login/',
        follow_redirects=True,
        json={'password': 'hopeless'})
    assert response.status_code == 422
    # Now neither
    response = client.post(
        '/api/v1/login/',
        follow_redirects=True,
        json={})
    assert response.status_code == 422
    # Let's try to login with disabled_user and make sure it yells at us
    response = client.post(
        '/api/v1/login/',
        follow_redirects=True,
        json={'user_name': 'disabled', 'password': 'banhammer'})
    assert response.status_code == 401
    # Make sure it still has no session token
    disabled_user = User.get_by_id(disabled_user_id)
    assert disabled_user.session_token is None
    # Okay, now lets actually log in
    response = client.post(
        '/api/v1/login/',
        follow_redirects=True,
        json={'user_name': 'test', 'password': 'weakpass'})
    assert response.status_code == 200
    # And make sure it gives us is what it's supposed to
    test_user = User.get_by_id(test_user_id)
    assert json.loads(response.data) == UserTokenSchema().dump(test_user)
    assert json.loads(response.data)['token'] == test_user.session_token

    # Let's save the token it gave us
    old_token = json.loads(response.data)['token']
    # sleep 1 second just to make sure any timestamps are different for token
    # generation
    sleep(1)
    # login again to make sure it gives us the old, but still valid token
    response = client.post(
        '/api/v1/login/',
        follow_redirects=True,
        json={'user_name': 'test', 'password': 'weakpass'})
    assert json.loads(response.data)['token'] == old_token
    # now let's pass force_renew to make sure it gives us a fresh token
    response = client.post(
        '/api/v1/login/',
        follow_redirects=True,
        json={'force_renew': True,
              'user_name': 'test',
              'password': 'weakpass'})
    assert json.loads(response.data)['token'] != old_token


def test_login_patch(client, test_user):
    """Functional test for login_patch."""
    # First lets get our token
    test_user_token = test_user.get_id()
    # Let's try to patch without a token
    response = client.patch(
        '/api/v1/login/',
        follow_redirects=True,
        json={'full_name': 'I am a test',
              'email': 'user@example.com',
              'password': 'howdypassword'})
    assert response.status_code == 403
    # Now let's make sure we can patch with the token.
    response = client.patch(
        '/api/v1/login/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)],
        json={'full_name': 'I am a test',
              'email': 'user@example.com',
              'password': 'howdypassword'})
    assert response.status_code == 200
    assert json.loads(response.data)['full_name'] == 'I am a test'
    assert json.loads(response.data)['email'] == 'user@example.com'
    assert test_user.verify_password('howdypassword') is True
    # Now let's make sure it yells if we're an LDAP user
    test_user.update(ldap_user=True)
    test_user_token = test_user.get_id()
    response = client.patch(
        '/api/v1/login/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)],
        json={'full_name': 'I am a test',
              'email': 'user@example.com',
              'password': 'howdypassword'})
    assert response.status_code == 400


def test_login_delete(client, test_user):
    """Functional test for login_post."""
    # First lets get our token
    test_user_id = test_user.id
    test_user_token = test_user.get_id()
    # Let's try to logout without a token
    response = client.delete(
        '/api/v1/login/',
        follow_redirects=True)
    assert response.status_code == 403
    # Now let's try with a wrong token
    response = client.delete(
        '/api/v1/login/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', 'notrealtoken')])
    assert response.status_code == 403
    # Okay, now lets actually log out
    response = client.delete(
        '/api/v1/login/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 205
    # And make sure it actually logged us out
    test_user = User.get_by_id(test_user_id)
    assert test_user.session_token is None
    assert test_user.session_token_expires_at is None

###############################################################################
# User Tests
###############################################################################


def test_users_list(client, test_user, test_users):
    """Functional test for users_list."""
    # First lets get our token
    test_user_token = test_user.get_id()
    # Let's make sure it yells at us if we don't give it a token
    response = client.get(
        '/api/v1/users/',
        follow_redirects=True)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.get(
        '/api/v1/users/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('list_users')
    response = client.get(
        '/api/v1/users/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    # We should have 11 users.
    assert len(json.loads(response.data)) == 11
    # Now let's try with a filter
    response = client.get(
        f'/api/v1/users/?name={test_user.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    # We should have 1 user.
    assert len(json.loads(response.data)) == 1
    assert json.loads(response.data)[0]['name'] == test_user.name


def test_users_post(client, test_user):
    """Functional test for users_post."""
    user_data = {
        'name': 'example',
        'full_name': 'Example User',
        'email': 'user@example.com',
        'enabled': True,
        'ldap_user': False,
        'password': 'myshinypassword'}
    # First lets get our token
    test_user_token = test_user.get_id()
    # Let's make sure it yells at us if we don't give it a token
    response = client.post(
        '/api/v1/users/',
        follow_redirects=True,
        json=user_data)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.post(
        '/api/v1/users/',
        follow_redirects=True,
        json=user_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('create_user')
    response = client.post(
        '/api/v1/users/',
        follow_redirects=True,
        json=user_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 201
    assert json.loads(response.data)['name'] == user_data['name']
    assert json.loads(response.data)['full_name'] == user_data['full_name']
    assert json.loads(response.data)['email'] == user_data['email']
    assert json.loads(response.data)['enabled'] == user_data['enabled']
    assert json.loads(response.data)['ldap_user'] == user_data['ldap_user']
    # Let's make sure it didn't short change us and actually made our user
    example_user = User.get_by_id_or_name('example')
    assert example_user.name == user_data['name']
    assert example_user.full_name == user_data['full_name']
    assert example_user.email == user_data['email']
    assert example_user.enabled == user_data['enabled']
    assert example_user.ldap_user == user_data['ldap_user']
    assert example_user.verify_password(user_data['password']) is True
    # Now try again to make sure it yells at us since the username is taken
    response = client.post(
        '/api/v1/users/',
        follow_redirects=True,
        json=user_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 400


def test_users_get(client, test_user, test_users):
    """Functional test for users_get."""
    # First lets get our token
    test_user_token = test_user.get_id()
    # Grab one of our generated users for these tests
    example_user = test_users[0]
    # Let's make sure it yells at us if we don't give it a token
    response = client.get(
        f'/api/v1/users/{example_user.id}',
        follow_redirects=True)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.get(
        f'/api/v1/users/{example_user.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('show_user')
    response = client.get(
        f'/api/v1/users/{example_user.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    # Make sure we got our user
    assert json.loads(response.data)['id'] == example_user.id
    assert json.loads(response.data)['name'] == example_user.name
    # Make sure it yells at us if the user is bogus
    response = client.get(
        f'/api/v1/users/fake_user',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404


def test_users_patch(client, test_user, test_users):
    """Functional test for users_patch."""
    user_data = {
        'name': 'example',
        'full_name': 'Example User',
        'email': 'user@example.com',
        'enabled': True,
        'ldap_user': False,
        'password': 'myshinypassword'}
    # First lets get our token
    test_user_token = test_user.get_id()
    # Grab one of our generated users for these tests
    example_user = test_users[0]
    # Let's make sure it yells at us if we don't give it a token
    response = client.patch(
        f'/api/v1/users/{example_user.id}',
        follow_redirects=True,
        json=user_data)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.patch(
        f'/api/v1/users/{example_user.id}',
        follow_redirects=True,
        json=user_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('update_user')
    response = client.patch(
        f'/api/v1/users/{example_user.id}',
        follow_redirects=True,
        json=user_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    # Make sure the return data is right
    assert json.loads(response.data)['name'] == user_data['name']
    assert json.loads(response.data)['full_name'] == user_data['full_name']
    assert json.loads(response.data)['email'] == user_data['email']
    assert json.loads(response.data)['enabled'] == user_data['enabled']
    assert json.loads(response.data)['ldap_user'] == user_data['ldap_user']
    # Make sure it actually updated the user
    assert example_user.name == user_data['name']
    assert example_user.full_name == user_data['full_name']
    assert example_user.email == user_data['email']
    assert example_user.enabled == user_data['enabled']
    assert example_user.ldap_user == user_data['ldap_user']
    assert example_user.verify_password(user_data['password']) is True
    # Make sure it yells at us if the user is bogus
    response = client.patch(
        f'/api/v1/users/fake_user',
        follow_redirects=True,
        json=user_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404


def test_users_delete(client, test_user, test_users):
    """Functional test for users_delete."""
    # First lets get our token
    test_user_token = test_user.get_id()
    # Grab one of our generated users for these tests
    example_user = test_users[0]
    # Let's go ahead and grab the ID now so we can verify it got nuked later
    example_user_id = example_user.id
    # Let's make sure it yells at us if we don't give it a token
    response = client.delete(
        f'/api/v1/users/{example_user.id}',
        follow_redirects=True)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.delete(
        f'/api/v1/users/{example_user.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('delete_user')
    response = client.delete(
        f'/api/v1/users/{example_user.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 204
    # Make sure the user is actually gone
    with pytest.raises(ValueError):
        User.get_by_id_or_name(example_user_id)
    # Trying again should give us a 404 since the user doesn't exist
    response = client.delete(
        f'/api/v1/users/{example_user.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404


###############################################################################
# Role Tests
###############################################################################


def test_roles_list(client, test_user, test_role, test_roles):
    """Functional test for roles_list."""
    # First lets get our token
    test_user_token = test_user.get_id()
    # Let's make sure it yells at us if we don't give it a token
    response = client.get(
        '/api/v1/roles/',
        follow_redirects=True)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.get(
        '/api/v1/roles/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('list_roles')
    response = client.get(
        '/api/v1/roles/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    # We should have 12 roles.
    assert len(json.loads(response.data)) == 12
    # Now let's try with a filter
    response = client.get(
        f'/api/v1/roles/?name={test_role.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    # We should have 1 role.
    assert len(json.loads(response.data)) == 1
    assert json.loads(response.data)[0]['name'] == test_role.name


def test_roles_post(client, test_user):
    """Functional test for roles_post."""
    role_data = {
        'name': 'example',
        'ldap_group': 'example',
        'description': 'The rolest role that ever roled.'}
    # First lets get our token
    test_user_token = test_user.get_id()
    # Let's make sure it yells at us if we don't give it a token
    response = client.post(
        '/api/v1/roles/',
        follow_redirects=True,
        json=role_data)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.post(
        '/api/v1/roles/',
        follow_redirects=True,
        json=role_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('create_role')
    response = client.post(
        '/api/v1/roles/',
        follow_redirects=True,
        json=role_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 201
    assert json.loads(response.data)['name'] == role_data['name']
    assert json.loads(response.data)['ldap_group'] == role_data['ldap_group']
    assert json.loads(response.data)['description'] == role_data['description']
    # Let's make sure it didn't short change us and actually made our role
    example_role = Role.get_by_id_or_name('example')
    assert example_role.name == role_data['name']
    assert example_role.ldap_group == role_data['ldap_group']
    assert example_role.description == role_data['description']
    # Now try again to make sure it yells at us since the role name is taken
    response = client.post(
        '/api/v1/roles/',
        follow_redirects=True,
        json=role_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 400


def test_roles_get(client, test_user, test_roles):
    """Functional test for roles_get."""
    # First lets get our token
    test_user_token = test_user.get_id()
    # Grab one of our generated roles for these tests
    example_role = test_roles[0]
    # Let's make sure it yells at us if we don't give it a token
    response = client.get(
        f'/api/v1/roles/{example_role.id}',
        follow_redirects=True)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.get(
        f'/api/v1/roles/{example_role.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('show_role')
    response = client.get(
        f'/api/v1/roles/{example_role.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    # Make sure we got our role
    assert json.loads(response.data)['id'] == example_role.id
    assert json.loads(response.data)['name'] == example_role.name
    # Make sure it yells at us if the role is bogus
    response = client.get(
        f'/api/v1/roles/fake_role',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404


def test_roles_patch(client, test_user, test_roles):
    """Functional test for roles_patch."""
    role_data = {
        'name': 'example',
        'ldap_group': 'example',
        'description': 'The rolest role that ever roled.'}
    # First lets get our token
    test_user_token = test_user.get_id()
    # Grab one of our generated roles for these tests
    example_role = test_roles[0]
    # Let's make sure it yells at us if we don't give it a token
    response = client.patch(
        f'/api/v1/roles/{example_role.id}',
        follow_redirects=True,
        json=role_data)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.patch(
        f'/api/v1/roles/{example_role.id}',
        follow_redirects=True,
        json=role_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('update_role')
    response = client.patch(
        f'/api/v1/roles/{example_role.id}',
        follow_redirects=True,
        json=role_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    # Make sure the return data is right
    assert json.loads(response.data)['name'] == role_data['name']
    assert json.loads(response.data)['ldap_group'] == role_data['ldap_group']
    assert json.loads(response.data)['description'] == role_data['description']
    # Make sure it actually updated the role
    assert example_role.name == role_data['name']
    assert example_role.ldap_group == role_data['ldap_group']
    assert example_role.description == role_data['description']
    # Make sure it yells at us if the role is bogus
    response = client.patch(
        f'/api/v1/roles/fake_user',
        follow_redirects=True,
        json=role_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404


def test_roles_delete(client, test_user, test_role):
    """Functional test for roles_delete."""
    # First lets get our token
    test_user_token = test_user.get_id()
    # Let's go ahead and grab the ID now so we can verify it got nuked later
    test_role_id = test_role.id
    # Let's make sure it yells at us if we don't give it a token
    response = client.delete(
        f'/api/v1/roles/{test_role.id}',
        follow_redirects=True)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.delete(
        f'/api/v1/roles/{test_role.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('delete_role')
    response = client.delete(
        f'/api/v1/roles/{test_role.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 204
    # Make sure the role is actually gone
    with pytest.raises(ValueError):
        Role.get_by_id_or_name(test_role_id)
    # Trying again should give us a 404 since the role doesn't exist
    response = client.delete(
        f'/api/v1/roles/{test_role.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404


###############################################################################
# Role Permission Tests
###############################################################################


def test_role_permissions_list(client, test_user, test_role):
    """Functional test for role_permissions_list."""
    # First lets get our token
    test_user_token = test_user.get_id()
    # Let's make sure it yells at us if we don't give it a token
    response = client.get(
        f'/api/v1/roles/{test_role.id}/permissions/',
        follow_redirects=True)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.get(
        f'/api/v1/roles/{test_role.id}/permissions/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('show_role')
    response = client.get(
        f'/api/v1/roles/{test_role.id}/permissions/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    # We should have 2 permissions.
    assert len(json.loads(response.data)) == 2
    # Now let's try with a filter
    response = client.get(
        f'/api/v1/roles/{test_role.id}/permissions/?name=test1',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    # We should have 1 permission.
    assert len(json.loads(response.data)) == 1
    assert json.loads(response.data)[0]['name'] == 'test1'
    # Check to make sure it yells at us if the role is bogus
    response = client.get(
        f'/api/v1/roles/fake_role/permissions/',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404


def test_role_permissions_post(client, test_user, test_role):
    """Functional test for role_permissions_post."""
    permission_data = {'name': 'permission-to-kill-9'}
    # First lets get our token
    test_user_token = test_user.get_id()
    # Let's make sure it yells at us if we don't give it a token
    response = client.post(
        f'/api/v1/roles/{test_role.id}/permissions/',
        follow_redirects=True,
        json=permission_data)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.post(
        f'/api/v1/roles/{test_role.id}/permissions/',
        follow_redirects=True,
        json=permission_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('update_role')
    response = client.post(
        f'/api/v1/roles/{test_role.id}/permissions/',
        follow_redirects=True,
        json=permission_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 201
    assert json.loads(response.data)['name'] == permission_data['name']
    # Let's make sure it didn't short change us
    example_permission = Permission.query.filter_by(
        role_id=test_role.id, name=permission_data['name']).first()
    assert example_permission.name == permission_data['name']
    # Now try again to make sure it yells at us since the role name is taken
    response = client.post(
        f'/api/v1/roles/{test_role.id}/permissions/',
        follow_redirects=True,
        json=permission_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 400
    # Check to make sure it yells at us if the role is bogus
    response = client.post(
        f'/api/v1/roles/fake_role/permissions/',
        follow_redirects=True,
        json=permission_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404


def test_role_permissions_get(client, test_user, test_role):
    """Functional test for role_permissions_get."""
    # First lets get our token
    test_user_token = test_user.get_id()
    # Grab one of our generated permissions for these tests
    test_permission = test_role.permissions[0]
    # Let's make sure it yells at us if we don't give it a token
    response = client.get(
        f'/api/v1/roles/{test_role.id}/permissions/{test_permission.name}',
        follow_redirects=True)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.get(
        f'/api/v1/roles/{test_role.id}/permissions/{test_permission.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('show_role')
    response = client.get(
        f'/api/v1/roles/{test_role.id}/permissions/{test_permission.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    assert json.loads(response.data)['id'] == test_permission.id
    assert json.loads(response.data)['name'] == test_permission.name
    # Should also work by id
    response = client.get(
        f'/api/v1/roles/{test_role.id}/permissions/{test_permission.id}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    assert json.loads(response.data)['id'] == test_permission.id
    assert json.loads(response.data)['name'] == test_permission.name
    # Make sure it yells at us if the permission is bogus
    response = client.get(
        f'/api/v1/roles/{test_role.id}/permissions/fake_permission',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404
    # Make sure it yells at us if the role is bogus
    response = client.get(
        f'/api/v1/roles/fake_role/permissions/fake_permission',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404


def test_role_permissions_patch(client, test_user, test_role):
    """Functional test for role_permissions_patch."""
    permission_data = {'name': 'permission-to-kill-9'}
    # First lets get our token
    test_user_token = test_user.get_id()
    # Grab one of our generated roles for these tests
    test_permission = test_role.permissions[0]
    # Let's make sure it yells at us if we don't give it a token
    response = client.patch(
        f'/api/v1/roles/{test_role.id}/permissions/{test_permission.name}',
        follow_redirects=True,
        json=permission_data)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.patch(
        f'/api/v1/roles/{test_role.id}/permissions/{test_permission.name}',
        follow_redirects=True,
        json=permission_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('update_role')
    response = client.patch(
        f'/api/v1/roles/{test_role.id}/permissions/{test_permission.name}',
        follow_redirects=True,
        json=permission_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 200
    # Make sure the return data is right
    assert json.loads(response.data)['name'] == permission_data['name']
    # Make sure it actually updated the permission
    assert test_permission.name == permission_data['name']
    # Make sure it yells at us if the permission is bogus
    response = client.patch(
        f'/api/v1/roles/{test_role.id}/permissions/fake_permission',
        follow_redirects=True,
        json=permission_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404
    # Check to make sure it also yells at us if the role is bogus
    response = client.patch(
        f'/api/v1/roles/fake_role/permissions/fake_permission',
        follow_redirects=True,
        json=permission_data,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404


def test_role_permissions_delete(client, test_user, test_role):
    """Functional test for role_permissions_delete."""
    # First lets get our token
    test_user_token = test_user.get_id()
    # Grab one of our test permissions
    test_permission = test_role.permissions[0]
    # Let's go ahead and grab the ID now so we can verify it got nuked later
    test_permission_id = test_permission.id
    assert Permission.get_by_id(test_permission_id) == test_permission
    # Let's make sure it yells at us if we don't give it a token
    response = client.delete(
        f'/api/v1/roles/{test_role.id}/permissions/{test_permission.name}',
        follow_redirects=True)
    assert response.status_code == 403
    # And with a user with no permissions
    response = client.delete(
        f'/api/v1/roles/{test_role.id}/permissions/{test_permission.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 403
    # Now let's add the right permission and try again.
    users_role = Role.get_by_id_or_name('users')
    users_role.add_permission('update_role')
    response = client.delete(
        f'/api/v1/roles/{test_role.id}/permissions/{test_permission.name}',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 204
    # Make sure the permission is actually gone
    with pytest.raises(ValueError):
        Permission.get_by_id(test_permission_id)
    # Make sure it yells at us if the permission is bogus
    response = client.delete(
        f'/api/v1/roles/{test_role.id}/permissions/fake_permission',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404
    # Check to make sure it also yells at us if the role is bogus
    response = client.delete(
        f'/api/v1/roles/fake_role/permissions/fake_permission',
        follow_redirects=True,
        headers=[('X-AUTH-TOKEN', test_user_token)])
    assert response.status_code == 404
