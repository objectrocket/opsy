from datetime import datetime
from time import time
from prettytable import PrettyTable
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from opsy.models import TimeStampMixin, BaseResource, NamedResource, OpsyQuery
from opsy.extensions import db
from opsy.exceptions import DuplicateError


role_mappings = db.Table(  # pylint: disable=invalid-name
    'role_mappings',
    db.Model.metadata,
    db.Column('role_id', db.String(36), db.ForeignKey('roles.id',
                                                      ondelete='CASCADE')),
    db.Column('user_id', db.String(36), db.ForeignKey('users.id',
                                                      ondelete='CASCADE')),
    db.Column('created_at', db.DateTime, default=datetime.utcnow()),
    db.Column('updated_at', db.DateTime, default=datetime.utcnow(),
              onupdate=datetime.utcnow()))


class Permission(BaseResource, TimeStampMixin, db.Model):

    __tablename__ = 'permissions'

    role_id = db.Column(db.String(36), db.ForeignKey('roles.id',
                                                     ondelete='CASCADE'))
    name = db.Column(db.String(128))

    __table_args__ = (
        db.UniqueConstraint('role_id', 'name'),
    )

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'role_id': self.role_id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)


class User(UserMixin, NamedResource, TimeStampMixin, db.Model):

    __tablename__ = 'users'

    backend = db.Column(db.String(20))
    full_name = db.Column(db.String(64))
    email = db.Column(db.String(64), index=True)
    password_hash = db.Column(db.String(128))
    session_token = db.Column(db.String(255))
    enabled = db.Column(db.Boolean, default=False)
    settings = db.relationship('UserSetting', cascade='all, delete-orphan',
                               backref='user', lazy='dynamic',
                               query_class=OpsyQuery, )
    roles = db.relationship('Role', secondary=role_mappings, backref='users')
    permissions = db.relationship('Permission',
                                  secondary='join(User, role_mappings, '
                                  'User.id == role_mappings.c.user_id).join'
                                  '(Role, role_mappings.c.role_id == Role.id)',
                                  primaryjoin='Role.id == Permission.role_id')

    __mapper_args__ = {
        'polymorphic_on': backend,
        'polymorphic_identity': 'internal'
    }

    __table_args__ = (
        db.UniqueConstraint('session_token', name='sess_uc'),
    )

    def __init__(self, name, enabled=0, full_name=None, email=None,
                 role_id=None, password=None, **kwargs):
        self.name = name
        self.enabled = enabled
        self.full_name = full_name
        self.email = email
        self.role_id = role_id
        if password:
            self.password = password

    def get_id(self):
        return self.get_session_token(current_app)

    def get_session_token(self, app, force_renew=False):
        ttl = app.config.opsy['session_token_ttl']
        data = self._decode_token(app, self.session_token)
        if data and int(data['expires_at']) > time() + ttl:
            force_renew = True  # renew the token, the ttl has been reduced
        if data and not force_renew:
            expires_at = int(data['expires_at'])
        else:
            seri = Serializer(
                app.config['SECRET_KEY'], expires_in=ttl)
            expires_at = int(time() + ttl)
            self.session_token = seri.dumps(
                {'id': self.id, 'expires_at': expires_at}).decode('ascii')
            self.save()
        return {'token': self.session_token,
                'expires_at': datetime.utcfromtimestamp(expires_at)}

    @classmethod
    def get_by_token(cls, app, token):
        data = cls._decode_token(app, token)
        if not data:
            return None
        return cls.get(id=data['id']).first()

    @staticmethod
    def _decode_token(app, token):
        if not token:
            return None
        seri = Serializer(app.config['SECRET_KEY'])
        try:
            data = seri.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        return data

    def pretty_print(self, all_attrs=False, ignore_attrs=None):
        super().pretty_print(all_attrs=False, ignore_attrs=None)
        print('\nSettings:')
        columns = ['id', 'key', 'value', 'created_at', 'updated_at']
        table = PrettyTable(columns)
        for setting in self.settings.all():  # pylint: disable=no-member
            setting_dict = setting.get_dict(all_attrs=True)
            table.add_row([setting_dict.get(x) for x in columns])
        print(table)

    @property
    def is_active(self):
        return self.enabled

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        self.session_token = None
        self.save()

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_setting(self, key, value):
        if self.get_setting_by_key(key):
            raise DuplicateError('Setting already exists with key "%s".' % key)
        return UserSetting.create(user_id=self.id, key=key, value=value).save()

    def remove_setting(self, key):
        return self.get_setting_by_key(key, error_on_none=True).delete()

    def modify_setting(self, key, value):
        return self.get_setting_by_key(key, error_on_none=True).update(
            value=value)

    def get_setting(self, key, error_on_none=False):
        setting = UserSetting.query.filter(UserSetting.user_id == self.id,
                                           UserSetting.key == key).first()
        if not setting and error_on_none:
            raise ValueError('No setting found with key "%s".' % key)
        return setting

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'roles': [x.name for x in self.roles],
            'permissions': [x.name for x in self.permissions],
            'email': self.email,
            'enabled': self.enabled,
            'full_name': self.full_name
        }


class UserSetting(BaseResource, TimeStampMixin, db.Model):

    __tablename__ = 'user_settings'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id',
                                                     ondelete='CASCADE'))
    key = db.Column(db.String(128))
    value = db.Column(db.String(128))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'key'),
    )

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

    description = db.Column(db.String(128))
    permissions = db.relationship('Permission', backref='role',
                                  cascade='all, delete-orphan',
                                  single_parent=True)

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

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'description': self.description,
            'permissions': [x.name for x in self.permissions],
            'users': [x.name for x in self.users]
        }
