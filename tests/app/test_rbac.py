import flask
import pytest
from flask_login import AnonymousUserMixin
from werkzeug.exceptions import Forbidden
from opsy.rbac import (is_logged_in, is_same_user, has_permission,
                       need_permission)


def test_is_logged_in(app, test_user):
    """Make sure the is logged in requirement works."""
    # Make sure we get false with the anon user.
    anon_user = AnonymousUserMixin()
    assert is_logged_in(anon_user) is False
    # ...but true if login is disabled
    app.config['LOGIN_DISABLED'] = True
    assert is_logged_in(anon_user) is True
    # Reset the flag
    app.config['LOGIN_DISABLED'] = False
    # Now let's use a test user and verify it's True
    assert is_logged_in(test_user) is True
    # ...but not true if we disable the account.
    test_user.update(enabled=False)
    assert is_logged_in(test_user) is False
    # ...but true if login is disabled.
    app.config['LOGIN_DISABLED'] = True
    assert is_logged_in(test_user) is True
    # Reset this since it's a session fixture.
    app.config['LOGIN_DISABLED'] = False


def test_is_same_user(app, test_user, mocker):
    """Make sure the is_same_user requirement works."""
    # First we need to mock the request object.
    view_args_mock = mocker.patch.object(flask.request, 'view_args')
    # Now this should return true
    view_args_mock.get.return_value = 'test'
    assert is_same_user(test_user) is True
    # ...but not this
    view_args_mock.get.return_value = 'not_test'
    assert is_same_user(test_user) is False


def test_has_permission(app, test_user, test_role):
    """Make sure has_permission works as expected."""
    # First we setup the test permission and an anon user
    test_permission = has_permission('test')
    anon_user = AnonymousUserMixin()
    # Let's disable login, these should both pass
    app.config['LOGIN_DISABLED'] = True
    assert test_permission(anon_user) is True
    assert test_permission(test_user) is True
    # Reset that and test again
    app.config['LOGIN_DISABLED'] = False
    # This should fail for the anon_user since base_permissions is empty
    assert test_permission(anon_user) is False
    # The test user isn't in a role so this should fail
    assert test_permission(test_user) is False
    # Now let's add add test to the base_permissions
    app.config.opsy['auth']['base_permissions'] = ['test']
    # This should now pass for both users
    assert test_permission(anon_user) is True
    assert test_permission(test_user) is True
    # Go ahead and reset that and test again with logged_in_permissions
    app.config.opsy['auth']['base_permissions'] = []
    app.config.opsy['auth']['logged_in_permissions'] = ['test']
    # This should now only pass for the test user
    assert test_permission(anon_user) is False
    assert test_permission(test_user) is True
    # Now let's reset that and add the user to a role with this permission
    app.config.opsy['auth']['logged_in_permissions'] = []
    test_role.add_user(test_user)
    test_role.add_permission('test')
    # This should pass since the user is in a role with this permission
    assert test_permission(test_user) is True


def test_need_permission(app, test_user, test_role):
    """Make sure the need_permission decorator works as expected."""

    # Let's make a test function and decorate it
    def test_func():
        return 'test function'

    test_decorated = need_permission('test')(test_func)
    # The resulting wrapped function should have an __rbac__ attribute with
    # the permission name in it.
    assert test_decorated.__rbac__['permission_needed'] == 'test'
    # Make sure it raises a forbidden since it's not aware of a user.
    with pytest.raises(Forbidden):
        test_decorated()
    # Now make it with on_fail. We don't really use it, but it should be
    # tested. This will just use the callable you provide it instead of raising
    # an exception.
    test_decorated = need_permission('test', on_fail=lambda: 'blah')(test_func)
    assert test_decorated() == 'blah'
    # Now let's recreate the decorated function with a user passed to it.
    # Usually you wouldn't pass the identity in like this, but it saves us
    # from having to mock things out for testing.
    test_decorated = need_permission('test', identity=test_user)(test_func)
    # Let's first make sure it doesn't allow this since our user doesn't have
    # the permission.
    with pytest.raises(Forbidden):
        test_decorated()
    # Now let's give to user permission and make sure it allows it
    test_role.add_user(test_user)
    test_role.add_permission('test')
    assert test_decorated() == 'test function'
    # Now let's give it another requirement with a permission the user doesn't
    # have
    test_decorated = need_permission(
        'test2', is_logged_in, identity=test_user)(test_func)
    # This should pass since the user is "logged in"
    assert test_decorated() == 'test function'
    # That last one will throw deprecation warnings until this is merged:
    # https://github.com/justanr/flask-allows/pull/45
