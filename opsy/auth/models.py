from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from opsy.auth.utils import create_token
from opsy.flask_extensions import db
from opsy.models import AwareDateTime, BaseModel, NamedModel, TimeStampMixin

###############################################################################
# Auth models
###############################################################################


class User(UserMixin, NamedModel, TimeStampMixin, db.Model):

    __tablename__ = 'users'

    full_name = db.Column(db.String(64))
    email = db.Column(db.String(64), index=True)
    password_hash = db.Column(db.String(128))
    session_token = db.Column(db.String(255), index=True)
    session_token_expires_at = db.Column(AwareDateTime)
    enabled = db.Column(db.Boolean, default=False)
    ldap_user = db.Column(db.Boolean, default=False)
    roles = db.relationship('Role', secondary='role_mappings',
                            lazy='joined', backref='users')

    __table_args__ = (
        db.UniqueConstraint('session_token', name='sess_uc'),
    )

    def __init__(self, name, enabled=1, full_name=None, email=None,
                 ldap_user=False, password=None):
        self.name = name
        self.enabled = enabled
        self.full_name = full_name
        self.email = email
        self.ldap_user = ldap_user
        if password:
            self.password = password

    @property
    def permissions(self):
        permissions = []
        for role in self.roles:
            for permission in role.permissions:
                permissions.append(permission)
        return permissions

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
        Permission.delete_by_role_and_id_or_name(self, permission_name)


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

    @classmethod
    def get_by_role_and_id_or_name(cls, role, id_or_name):
        obj = cls.query.filter(db.and_(cls.role_id == role.id, db.or_(
            cls.name == id_or_name, cls.id == id_or_name))).first()
        if not obj:
            raise ValueError('No %s found with name or id "%s".' %
                             (cls.__name__, id_or_name))
        return obj

    @classmethod
    def delete_by_role_and_id_or_name(cls, role, id_or_name, **kwargs):
        return cls.get_by_role_and_id_or_name(
            role, id_or_name).delete(**kwargs)

    @classmethod
    def update_by_role_and_id_or_name(cls, role, id_or_name, **kwargs):
        return cls.get_by_role_and_id_or_name(
            role, id_or_name).update(**kwargs)

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.name}>'
