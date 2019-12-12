from faker import Faker
from opsy.auth.models import Role, User
from opsy.utils import get_valid_permissions


def test_user():
    test_user = User.create(
        name='test', full_name='Test User', password='weakpass')
    test_role = Role.create(name='users')
    test_role.add_user(test_user)
    return test_user


def disabled_user():
    return User.create(
        name='disabled', full_name='Disabled User', password='banhammer',
        enabled=0)


def admin_user():
    admin_user = User.create(
        name='admin', full_name='Admin User', password='password123')
    admin_role = Role.create(name='admins')
    for permission in get_valid_permissions():
        admin_role.add_permission(permission)
    admin_role.add_user(admin_user)
    return admin_user


def test_users(number=10):
    fake = Faker(locale='en_US')
    fake.seed(8675309)
    users = []
    for x in range(0, number):
        users.append(User.create(name=fake.user_name(), full_name=fake.name(),
                                 password=fake.password()))
    return users


def test_role():
    test_role = Role.create(name='test')
    test_role.add_permission('test1')
    test_role.add_permission('test2')
    return test_role


def test_roles(number=10):
    fake = Faker(locale='en_US')
    fake.seed(8675309)
    roles = []
    for x in range(0, number):
        roles.append(Role.create(name=fake.domain_word()))
    return roles
