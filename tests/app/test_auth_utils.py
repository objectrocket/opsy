from opsy.auth.utils import (login, logout, create_token, verify_token,
                             load_user, load_user_from_request)
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from datetime import datetime


def test_login(test_user, disabled_user):
    # Test that test_user can login
    assert login('test', 'weakpass') == test_user
    # Test that invalid username is rejected
    assert login('invalid_user', 'password') is False
    # Test that invalid password is rejected
    assert login('test', 'password') is False
    # Test invalid user cannot login
    assert login('disabled', 'banhammer') is False


def test_local_login(test_user, disabled_user):
    # Test that test_user can login
    assert login('test', 'weakpass') == test_user
    # Now let's set this to be an ldap user and make sure it rejects it
    test_user.update(ldap_user=True)
    assert login('test', 'weakpass') is False
    test_user.update(ldap_user=False)
    # Test that invalid username is rejected
    assert login('invalid_user', 'password') is False
    # Test that invalid password is rejected
    assert login('test', 'password') is False
    # Test invalid user cannot login
    assert login('disabled', 'banhammer') is False


def test_logout(test_user):
    # Test that logout is processed successfully
    create_token(test_user)
    logout(test_user)
    assert test_user.session_token is None
    # Test that logout handles empty input
    assert logout('') is None


def test_create_token(test_user):
    assert test_user.session_token is None
    assert test_user.session_token_expires_at is None
    # Test that a token is created successfully
    create_token(test_user)
    assert test_user.session_token is not None
    assert test_user.session_token_expires_at is not None
    # Testing force_renew returns as expected
    assert create_token(test_user, force_renew=True) == test_user


def test_verify_token(test_user):
    # Test data
    expired_serializer = Serializer(
        current_app.config['SECRET_KEY'], expires_in=-1)
    expired_token = expired_serializer.dumps(
        {'id': test_user.id}).decode('ascii')
    bad_serializer = Serializer('12345')
    bad_token = bad_serializer.dumps({'id': test_user.id}).decode('ascii')
    good_serializer = Serializer(
        current_app.config['SECRET_KEY'],
        expires_in=current_app.config.opsy['auth']['session_token_ttl'])
    bad_id_token = good_serializer.dumps({'id': '12345'}).decode('ascii')
    # Testing the null case
    assert verify_token(None) is None
    # Test verifying with no token
    assert verify_token(test_user) is None
    # Test verifying with expired token
    test_user.update(session_token=expired_token)
    assert verify_token(test_user) is None
    # Test verifying with bad token
    test_user.update(session_token=bad_token)
    assert verify_token(test_user) is None
    # Test reducing the TTL
    create_token(test_user)
    current_ttl = current_app.config.opsy['auth']['session_token_ttl']
    current_app.config.opsy['auth']['session_token_ttl'] = -1
    assert verify_token(test_user) is None
    current_app.config.opsy['auth']['session_token_ttl'] = current_ttl
    # Test the happy path before we mess with the session token
    assert verify_token(test_user) == test_user
    # Test mismatch in token id and user.id
    orig_token = test_user.session_token
    test_user.update(session_token=bad_id_token)
    assert verify_token(test_user) is None
    test_user.update(session_token=orig_token)
    # Test mismatch in token expiration times
    test_user.update(session_token_expires_at=datetime.now())
    assert verify_token(test_user) is None


def test_load_user(test_user):
    create_token(test_user)
    assert load_user(test_user.session_token) == test_user


def test_load_user_from_request(test_user):
    class testRequest():
        def __init__(self, headers={}):
            self.headers = headers

    create_token(test_user)
    req = testRequest(headers={'X-AUTH-TOKEN': test_user.session_token})
    assert load_user_from_request(req) == test_user
