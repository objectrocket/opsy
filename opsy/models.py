import uuid
from collections import OrderedDict
from datetime import datetime
from flask_sqlalchemy import BaseQuery
from flask import abort, json
from prettytable import PrettyTable
from sqlalchemy.orm.base import _entity_descriptor
from opsy.flask_extensions import db
from opsy.utils import get_filters_list, print_property_table
from opsy.exceptions import DuplicateError


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
            obj_dict = obj.get_dict(all_attrs=True)
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
