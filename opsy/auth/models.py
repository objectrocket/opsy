from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from opsy.auth.utils import create_token
from opsy.flask_extensions import db
from opsy.models import BaseModel, NamedModel, TimeStampMixin

###############################################################################
# Auth models
###############################################################################


class User(UserMixin, NamedModel, TimeStampMixin, db.Model):

    __tablename__ = 'users'

    full_name = db.Column(db.String(64))
    email = db.Column(db.String(64), index=True)
    password_hash = db.Column(db.String(128))
    session_token = db.Column(db.String(255), index=True)
    session_token_expires_at = db.Column(db.DateTime)
    enabled = db.Column(db.Boolean, default=False)
    roles = db.relationship('Role', secondary='role_mappings',
                            lazy='joined', backref='users')
    permissions = db.relationship('Permission', lazy='joined',
                                  secondary='join(Permission, Role, '
                                  'Permission.role_id == Role.id).join('
                                  'role_mappings, '
                                  'Role.id == role_mappings.c.role_id)')

    __table_args__ = (
        db.UniqueConstraint('session_token', name='sess_uc'),
    )

    def __init__(self, name, enabled=1, full_name=None, email=None,
                 password=None):
        self.name = name
        self.enabled = enabled
        self.full_name = full_name
        self.email = email
        if password:
            self.password = password

    def get_id(self):
        create_token(self)
        return self.session_token

    @classmethod
    def get_by_token(cls, token):
        if not token:
            return None
        user = cls.query.filter(cls.session_token == token).first()
        if not user:
            return None
        return user

    @property
    def is_active(self):
        return self.enabled

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        self.session_token = None
        self.save()

    def verify_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)


class Role(NamedModel, TimeStampMixin, db.Model):

    __tablename__ = 'roles'

    ldap_group = db.Column(db.String(128), index=True)
    description = db.Column(db.Text)
    permissions = db.relationship('Permission', backref='role',
                                  cascade='all, delete-orphan')

    def add_user(self, user):
        if user in self.users:
            raise ValueError('User "%s" already added to role "%s".' % (
                user.name, self.name))
        self.users.append(user)
        self.save()

    def remove_user(self, user):
        if user not in self.users:
            raise ValueError('User "%s" not in role "%s".' % (
                user.name, self.name))
        self.users.remove(user)
        self.save()

    def add_permission(self, permission_name):
        if permission_name in [x.name for x in self.permissions]:
            raise ValueError('Permission "%s" already added to role "%s".' % (
                permission_name, self.name))
        permission_obj = Permission(
            role_id=self.id, name=permission_name)
        permission_obj.save()
        return permission_obj

    def remove_permission(self, permission_name):
        if permission_name not in [x.name for x in self.permissions]:
            raise ValueError('Permission "%s" not in role "%s".' % (
                permission_name, self.name))
        Permission.query.filter(
            Permission.role_id == self.id,
            Permission.name == permission_name).delete()
        db.session.commit()


class RoleMappings(BaseModel, TimeStampMixin, db.Model):

    __tablename__ = 'role_mappings'

    role_id = db.Column(
        db.String(36), db.ForeignKey('roles.id', ondelete='CASCADE'),
        index=True, nullable=False)
    user_id = db.Column(
        db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'),
        index=True, nullable=False)

    role = db.relationship('Role')
    user = db.relationship('User')


class Permission(BaseModel, TimeStampMixin, db.Model):

    __tablename__ = 'permissions'

    role_id = db.Column(db.String(36), db.ForeignKey(
        'roles.id', ondelete='CASCADE'), index=True, nullable=False)
    name = db.Column(db.String(128), index=True, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('role_id', 'name'),
    )

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.name}>'
