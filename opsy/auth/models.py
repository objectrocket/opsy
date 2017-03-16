from datetime import datetime, timezone
from time import time
from prettytable import PrettyTable
from flask import current_app
from flask_login import UserMixin, login_user, logout_user
from flask_principal import identity_changed, Identity, AnonymousIdentity
from flask_ldap3_login import AuthenticationResponseStatus
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from opsy.models import TimeStampMixin, BaseResource, NamedResource, OpsyQuery
from opsy.flask_extensions import db, ldap_manager
from opsy.exceptions import DuplicateError


role_mappings = db.Table(  # pylint: disable=invalid-name
    'role_mappings',
    db.Model.metadata,
    db.Column('role_id', db.String(36),
              db.ForeignKey('roles.id', ondelete='CASCADE'), index=True),
    db.Column('user_id', db.String(36),
              db.ForeignKey('users.id', ondelete='CASCADE'), index=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow()),
    db.Column('updated_at', db.DateTime, default=datetime.utcnow(),
              onupdate=datetime.utcnow()))


class Permission(BaseResource, TimeStampMixin, db.Model):

    __tablename__ = 'permissions'

    role_id = db.Column(db.String(36), db.ForeignKey(
        'roles.id', ondelete='CASCADE'), index=True)
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

    full_name = db.Column(db.String(64))
    email = db.Column(db.String(64), index=True)
    password_hash = db.Column(db.String(128))
    session_token = db.Column(db.String(255), index=True)
    session_token_expires_at = db.Column(db.DateTime)
    enabled = db.Column(db.Boolean, default=False)
    settings = db.relationship('UserSetting', cascade='all, delete-orphan',
                               backref='user', lazy='joined',
                               query_class=OpsyQuery, )
    roles = db.relationship('Role', secondary=role_mappings,
                            lazy='joined', backref='users')
    permissions = db.relationship('Permission', backref='users',
                                  lazy='joined',
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

    @classmethod
    def login(cls, app, username, password, remember=False, force=False,
              fresh=True):
        if app.config.opsy['enable_ldap']:
            result = ldap_manager.authenticate(username, password)
            if not result.status == AuthenticationResponseStatus.success:
                return False
            full_name_attr = app.config.opsy['ldap_user_full_name_attr']
            email_attr = app.config.opsy['ldap_user_email_attr']
            group_name_attr = app.config.opsy['ldap_group_name_attr']
            email = result.user_info[email_attr]
            full_name = result.user_info[full_name_attr]
            user = cls.query.wtfilter_by(name=result.user_id).first()
            if not user:
                user = cls.create(username, email=email, full_name=full_name)
            else:
                user.update(email=email, full_name=full_name)
            groups = [x[group_name_attr] for x in result.user_groups]
            for role in user.roles:
                if role.ldap_group:
                    user.roles.remove(role)
            for role in Role.query.filter(Role.ldap_group.in_(groups)).all():
                user.roles.append(role)
            user.save()
        else:
            user = cls.query.wtfilter_by(name=username).first()
            if not user:
                return False
            if not user.verify_password(password):
                return False
        if login_user(user, remember=remember):
            identity_changed.send(
                app._get_current_object(),  # pylint: disable=W0212
                identity=Identity(user.id))
            return user.get_session_token(app)
        return False

    def logout(self, app):
        self.session_token = None
        self.session_token_expires_at = None
        if app.config.opsy['enable_ldap']:
            for role in self.roles:
                if role.ldap_group:
                    self.roles.remove(role)
        self.save()
        logout_user()
        identity_changed.send(
            current_app._get_current_object(),  # pylint: disable=W0212
            identity=AnonymousIdentity())

    def get_id(self):
        return self.get_session_token(current_app).get('token')

    def get_session_token(self, app, force_renew=False):
        if force_renew or not self.verify_token(app):
            self.create_token(app)
        return {'id': self.id,
                'name': self.name,
                'token': self.session_token,
                'expires_at': self.session_token_expires_at}

    @classmethod
    def get_by_token(cls, app, token):
        if not token:
            return None
        user = cls.query.filter(cls.session_token == token).first()
        if user and user.verify_token(app):
            return user
        return None

    def verify_token(self, app):  # pylint: disable=R0911
        ttl = app.config.opsy['session_token_ttl']
        seri = Serializer(app.config['SECRET_KEY'])
        try:
            data, header = seri.loads(self.session_token, return_header=True)
        except TypeError:
            return False  # we don't currently have a token
        except SignatureExpired:
            return False  # valid token, but expired
        except BadSignature:
            return False  # invalid token
        if int(self.session_token_expires_at.replace(
                tzinfo=timezone.utc).timestamp()) > time() + ttl:
            return False  # ttl in config has been reduced
        # These next two shouldn't ever happen
        if data.get('id') != self.id:
            return False  # user id doesn't match token payload
        if self.session_token_expires_at != datetime.utcfromtimestamp(
                header.get('exp')):
            return False  # expire times don't match
        return True

    def create_token(self, app):
        ttl = app.config.opsy['session_token_ttl']
        seri = Serializer(
            app.config['SECRET_KEY'], expires_in=ttl)
        self.session_token = seri.dumps({'id': self.id}).decode('ascii')
        _, header = seri.loads(self.session_token, return_header=True)
        self.session_token_expires_at = datetime.utcfromtimestamp(
            header.get('exp'))
        self.save()

    def pretty_print(self, all_attrs=False, ignore_attrs=None):
        super().pretty_print(all_attrs=False, ignore_attrs=None)
        print('\nSettings:')
        columns = ['id', 'key', 'value', 'created_at', 'updated_at']
        table = PrettyTable(columns)
        for setting in self.settings:  # pylint: disable=no-member
            setting_dict = setting.get_dict(all_attrs=True)
            table.add_row([setting_dict.get(x) for x in columns])
        print(table)

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
        return check_password_hash(self.password_hash, password)

    def add_setting(self, key, value):
        if not key:
            raise ValueError('Setting must have a key.')
        if self.get_setting(key):
            raise DuplicateError('Setting already exists with key "%s".' % key)
        return UserSetting.create(user_id=self.id, key=key, value=value).save()

    def remove_setting(self, key):
        return self.get_setting(key, error_on_none=True).delete()

    def modify_setting(self, key, value):
        return self.get_setting(key, error_on_none=True).update(
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
            'permissions': list(set([x.name for x in self.permissions])),  # dedup
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

    ldap_group = db.Column(db.String(128))
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
            'ldap_group': self.ldap_group,
            'description': self.description,
            'permissions': [x.name for x in self.permissions],
            'users': [x.name for x in self.users]
        }
