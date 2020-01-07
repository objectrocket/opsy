import pytest
from opsy.auth.models import User, Permission, RoleMappings


def test_user_model(test_user, test_users):
    """Test User to make sure it works correctly."""
    # Test creating a token and lookup by token
    token = test_user.get_id()
    assert token == test_user.session_token
    assert User.get_by_token(token) == test_user
    assert User.get_by_token('thisisgarbagedata') is None
    # Test is_active
    test_user.update(enabled=False)
    assert test_user.is_active == test_user.enabled == 0
    test_user.update(enabled=True)
    assert test_user.is_active == test_user.enabled == 1
    # Test that verify password returns false when we don't have a password
    test_user.update(password_hash=None)
    assert test_user.verify_password(None) is False
    assert test_user.verify_password('testing123') is False
    with pytest.raises(AttributeError, match=r'.*not a readable.*'):
        test_user.password
    test_user.update(password='testing123')
    assert test_user.verify_password('testing123') is True
    assert test_user.verify_password('testing123567') is False


def test_role_model(test_user, test_users, test_role, test_roles):
    """Test Role to make sure it works correctly."""
    # Test add_user
    test_role.add_user(test_user)
    assert test_user in test_role.users
    assert RoleMappings.query.filter_by(
        user_id=test_user.id, role_id=test_role.id).first() is not None
    # Make sure it yells at us if the user is already in the role
    with pytest.raises(ValueError):
        test_role.add_user(test_user)
    # Test remove_user
    test_role.remove_user(test_user)
    assert test_user not in test_role.users
    # Make sure it yells at us if the user isn't in the role
    with pytest.raises(ValueError):
        test_role.remove_user(test_user)
    # Test add_permission
    test_permission = test_role.add_permission('permission-to-kill-9')
    assert test_permission in test_role.permissions
    assert Permission.query.filter_by(
        role_id=test_role.id, name='permission-to-kill-9').first() == \
        test_permission
    # Make sure it yells at us if the permission already exists
    with pytest.raises(ValueError):
        test_role.add_permission('permission-to-kill-9')
    # Let's check the permission __repr__
    assert test_permission.__repr__() == \
        f'<{test_permission.__class__.__name__} {test_permission.name}>'
    # Let's add the user back and make sure they see the permission too
    test_role.add_user(test_user)
    assert test_permission in test_user.permissions
    # Test remove_permission
    test_role.remove_permission('permission-to-kill-9')
    assert 'permission-to-kill-9' not in \
        [x.name for x in test_role.permissions]
    assert Permission.query.filter_by(
        role_id=test_role.id, name='permission-to-kill-9').first() is None
    # Make sure it yells at us if the permission doesn't exists
    with pytest.raises(ValueError):
        test_role.remove_permission('permission-to-kill-9')
    # And make sure the user also doesn't see it
    assert 'permission-to-kill-9' not in \
        [x.name for x in test_user.permissions]
    # Let's test the secondary tables
    sad_permission = test_role.add_permission('sadbois')
    test_user_id = test_user.id
    sad_permission_id = sad_permission.id
    role_mapping_id = RoleMappings.query.filter_by(
        user_id=test_user.id, role_id=test_role.id).first().id
    assert sad_permission in test_user.permissions
    # Now we'll make sure the secondary table assets are cleaned up
    test_role.delete()
    assert User.query.filter_by(id=test_user_id).first() is not None
    assert sad_permission not in test_user.permissions
    assert RoleMappings.query.filter_by(id=role_mapping_id).first() is None
    assert Permission.query.filter_by(id=sad_permission_id).first() is None
