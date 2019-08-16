import json
from opsy.auth.models import User
from opsy.auth.schema import UserTokenSchema


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
