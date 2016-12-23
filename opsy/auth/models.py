from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
# from itsdangerous import (TimedJSONWebSignatureSerializer
#                           as Serializer, BadSignature, SignatureExpired)
from opsy.db import db, TimeStampMixin, DictOut, BaseResource, NamedResource


role_mappings = db.Table(  # pylint: disable=invalid-name
    'role_mappings',
    db.Model.metadata,
    db.Column('role_id', db.String(36), db.ForeignKey('roles.id')),
    db.Column('user_id', db.String(36), db.ForeignKey('users.id')),
    db.Column('created_at', db.DateTime, default=datetime.utcnow()),
    db.Column('updated_at', db.DateTime, default=datetime.utcnow(),
              onupdate=datetime.utcnow()))


class PermissionMapping(BaseResource, TimeStampMixin, db.Model):

    __tablename__ = 'permission_mappings'
    query_class = DictOut

    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'))
    permission_name = db.Column(db.String(128))

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'role_id': self.role_id,
            'permission_name': self.permission_name,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class User(UserMixin, NamedResource, TimeStampMixin, db.Model):

    __tablename__ = 'users'
    query_class = DictOut

    full_name = db.Column(db.String(64))
    email = db.Column(db.String(64), index=True)
    password_hash = db.Column(db.String(128))
    enabled = db.Column(db.Boolean, default=False)
    settings = db.relationship('UserSetting')
    roles = db.relationship(
        'Role', secondary=role_mappings, backref='users')
    # permissions =

    def __init__(self, name, enabled=0, full_name=None, email=None,
                 role_id=None, password=None, **kwargs):
        self.name = name
        self.enabled = enabled
        self.full_name = full_name
        self.email = email
        self.role_id = role_id
        if password:
            self.password = password

    @classmethod
    def filter(cls, names=None, emails=None):
        filters = ((names, cls.name),
                   (emails, cls.email))
        return cls.get(filters=filters)

    @property
    def is_active(self):
        return self.enabled

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        self.save()

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_setting_by_key(self, key):
        return UserSetting.query.filter(UserSetting.key == key,
                                        UserSetting.user_id == self.id).first()

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'roles': [x.name for x in self.roles],
            'email': self.email,
            'enabled': self.enabled,
            'full_name': self.full_name
        }


class UserSetting(BaseResource, TimeStampMixin, db.Model):

    __tablename__ = 'user_settings'
    query_class = DictOut

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    key = db.Column(db.String(128))
    value = db.Column(db.String(128))

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class Role(NamedResource, TimeStampMixin, db.Model):

    __tablename__ = 'roles'
    query_class = DictOut

    description = db.Column(db.String(128))
    permissions = db.relationship('PermissionMapping')

    def add_user(self, user):
        self.users.append(user)
        self.save()

    def remove_user(self, user):
        self.users.remove(user)
        self.save()

    def add_permission(self, permission_name):
        if permission_name in [x.permission_name for x in self.permissions]:
            raise ValueError('Permission "%s" already added to role "%s".' % (
                permission_name, self.name))
        permission_obj = PermissionMapping(
            role_id=self.id, permission_name=permission_name)
        permission_obj.save()
        return permission_obj

    def remove_permission(self, permission_name):
        if permission_name not in [x.permission_name for x in self.permissions]:
            raise ValueError('Permission "%s" not in role "%s".' % (
                permission_name, self.name))
        PermissionMapping.query.filter(
            PermissionMapping.role_id == self.id,
            PermissionMapping.permission_name == permission_name).delete()
        db.session.commit()

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'description': self.description,
            'permissions': [x.permission_name for x in self.permissions],
            'users': [x.name for x in self.users]
        }
