import uuid
from collections import OrderedDict
from datetime import datetime
from prettytable import PrettyTable
from flask import abort, json
from flask_login import UserMixin
from flask_sqlalchemy import BaseQuery
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm.base import _entity_descriptor
from opsy.flask_extensions import db
from opsy.exceptions import DuplicateError
from opsy.utils import get_filters_list, print_property_table


###############################################################################
# Base models
###############################################################################


class TimeStampMixin(object):
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow(),
                           onupdate=datetime.utcnow())


class OpsyQuery(BaseQuery):

    def wtfilter_by(self, prune_none_values=False, **kwargs):
        if prune_none_values:
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
        filters = []
        for key, value in kwargs.items():
            descriptor = _entity_descriptor(self._joinpoint_zero(), key)
            if isinstance(value, str):
                descriptor = _entity_descriptor(self._joinpoint_zero(), key)
                filters.extend(get_filters_list([(value, descriptor)]))
            else:
                filters.append(descriptor == value)
        return self.filter(*filters)

    def get_or_fail(self, ident):
        obj = self.get(ident)
        if obj is None:
            raise ValueError
        return obj

    def first_or_fail(self):
        obj = self.first()
        if obj is None:
            raise ValueError
        return obj

    def all_dict_out(self, **kwargs):
        return [x.get_dict(**kwargs) for x in self]

    def all_dict_out_or_404(self, **kwargs):
        dict_list = self.all_dict_out(**kwargs)
        if not dict_list:
            abort(404)
        return dict_list

    def pretty_list(self, columns=None):
        if not columns:
            columns = self._joinpoint_zero().class_.__table__.columns.keys()
        table = PrettyTable(columns)
        for obj in self:
            obj_dict = obj.get_dict()
            table.add_row([obj_dict.get(x) for x in columns])
        print(table)


class BaseResource(object):

    query_class = OpsyQuery

    id = db.Column(db.String(36),  # pylint: disable=invalid-name
                   default=lambda: str(uuid.uuid4()), primary_key=True)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        return obj.save()

    @classmethod
    def delete_by_id(cls, obj_id):
        return cls.query.get(obj_id).first_or_fail().delete()

    @classmethod
    def update_by_id(cls, obj_id, prune_none_values=True, **kwargs):
        return cls.query.get(obj_id).first_or_fail().update(
            prune_none_values=prune_none_values, **kwargs)

    @property
    def dict_out(self):
        return OrderedDict([(key, getattr(self, key))
                            for key in self.__table__.columns.keys()])  # pylint: disable=no-member

    def pretty_print(self, all_attrs=False, ignore_attrs=None):
        properties = [(key, value) for key, value in self.get_dict(  # pylint: disable=no-member
            all_attrs=all_attrs).items()]  # pylint: disable=no-member
        print_property_table(properties, ignore_attrs=ignore_attrs)

    def update(self, commit=True, prune_none_values=True, **kwargs):
        kwargs.pop('id', None)
        for key, value in kwargs.items():
            if value is None and prune_none_values is True:
                continue
            setattr(self, key, value)
        return self.save() if commit else self

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        db.session.delete(self)
        return commit and db.session.commit()

    def get_dict(self, jsonify=False, serialize=False, pretty_print=False,
                 all_attrs=False, truncate=False, **kwargs):
        dict_out = self.dict_out
        if all_attrs:
            attr_dict = OrderedDict([(x.key, getattr(self, x.key))
                                     for x in self.__table__.columns])  # pylint: disable=no-member
            dict_out.update(attr_dict)
        if truncate:
            if 'output' in dict_out:
                dict_out['output'] = (dict_out['output'][:100] + '...') if \
                    len(dict_out['output']) > 100 else dict_out['output']
        if jsonify:
            if pretty_print:
                return json.dumps(dict_out, indent=4)
            return json.dumps(dict_out)
        if serialize:
            dict_out = json.loads(json.dumps(dict_out))
        return dict_out

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.id)


class NamedResource(BaseResource):

    name = db.Column(db.String(128), unique=True, index=True)

    def __init__(self, name, **kwargs):
        self.name = name
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def create(cls, name, *args, obj_class=None, **kwargs):
        if cls.query.filter_by(name=name).first():
            raise DuplicateError('%s already exists with name "%s".' % (
                cls.__name__, name))
        if obj_class:
            obj = obj_class(name, *args, **kwargs)
        else:
            obj = cls(name, *args, **kwargs)
        return obj.save()

    @classmethod
    def delete_by_name(cls, obj_name):
        return cls.query.filter_by(name=obj_name).first_or_fail().delete()

    @classmethod
    def update_by_name(cls, obj_name, prune_none_values=True, **kwargs):
        return cls.query.filter_by(name=obj_name).first_or_fail().update(
            prune_none_values=prune_none_values, **kwargs)

    @classmethod
    def get_by_id_or_name(cls, obj_id_or_name, error_on_none=False):
        obj = cls.query.filter(db.or_(
            cls.name == obj_id_or_name, cls.id == obj_id_or_name)).first()
        if not obj and error_on_none:
            raise ValueError('No %s found with name or id "%s".' %
                             (cls.__name__, obj_id_or_name))
        return obj

    @classmethod
    def delete_by_id_or_name(cls, obj_id_or_name):
        return cls.get_by_id_or_name(obj_id_or_name,
                                     error_on_none=True).delete()

    @classmethod
    def update_by_id_or_name(cls, obj_id_or_name, **kwargs):
        return cls.get_by_id_or_name(obj_id_or_name,
                                     error_on_none=True).update(**kwargs)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)


###############################################################################
# Auth models
###############################################################################


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
        from opsy.auth import create_token
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
        if not self.password_hash:
            return False
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
        return OrderedDict([
            ('id', self.id),
            ('name', self.name),
            ('created_at', self.created_at),
            ('updated_at', self.updated_at),
            ('roles', [x.name for x in self.roles]),
            ('permissions', list(
                set([x.name for x in self.permissions]))),  # dedup
            ('email', self.email),
            ('enabled', self.enabled),
            ('full_name', self.full_name)
        ])


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
        return OrderedDict([
            ('id', self.id),
            ('user_id', self.user_id),
            ('key', self.key),
            ('value', self.value),
            ('created_at', self.created_at),
            ('updated_at', self.updated_at)
        ])


class Role(NamedResource, TimeStampMixin, db.Model):

    __tablename__ = 'roles'

    ldap_group = db.Column(db.String(128))
    description = db.Column(db.String(128))
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

    @property
    def dict_out(self):
        return OrderedDict([
            ('id', self.id),
            ('name', self.name),
            ('created_at', self.created_at),
            ('updated_at', self.updated_at),
            ('ldap_group', self.ldap_group),
            ('description', self.description),
            ('permissions', [x.name for x in self.permissions]),
            ('users', [x.name for x in self.users])
        ])


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
        return OrderedDict([
            ('id', self.id),
            ('role_id', self.role_id),
            ('name', self.name),
            ('created_at', self.created_at),
            ('updated_at', self.updated_at)
        ])

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)
