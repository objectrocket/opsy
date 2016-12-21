import uuid
from datetime import datetime
from flask_sqlalchemy import BaseQuery, SQLAlchemy
from flask import abort
from flask import json
from opsy.utils import get_filters_list
from opsy.exceptions import DuplicateName


db = SQLAlchemy()  # pylint: disable=invalid-name


class TimeStampMixin(object):
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow(),
                           onupdate=datetime.utcnow())


class DictOut(BaseQuery):

    def all_dict_out(self, **kwargs):
        return [x.get_dict(**kwargs) for x in self]

    def all_dict_out_or_404(self, **kwargs):
        dict_list = self.all_dict_out(**kwargs)
        if not dict_list:
            abort(404)
        return dict_list


class BaseResource(object):

    query_class = DictOut

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
    def get(cls, filters=None):
        if filters:
            filters_list = get_filters_list(filters)
            return cls.query.filter(*filters_list)
        else:
            return cls.query

    @classmethod
    def get_by_id(cls, obj_id):
        obj = cls.query.filter(cls.id == obj_id).first()
        if not obj:
            raise KeyError('No %s found with id "%s"' % (cls.__name__, obj_id))
        return obj

    @classmethod
    def delete_by_id(cls, obj_id):
        return cls.get_by_id(obj_id).delete()

    @classmethod
    def update_by_id(cls, obj_id, **kwargs):
        return cls.get_by_id(obj_id).update(**kwargs)

    @property
    def dict_out(self):
        return {}

    def update(self, commit=True, **kwargs):
        kwargs.pop('id', None)
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)
        return commit and self.save() or self

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        db.session.delete(self)
        return commit and db.session.commit()

    def get_dict(self, jsonify=False, serialize=False, pretty_print=False,
                 all_attrs=False, **kwargs):
        dict_out = self.dict_out
        if all_attrs:
            attr_dict = {x.key: getattr(self, x.key)
                         for x in self.__table__.columns}  # pylint: disable=no-member
            dict_out.update(attr_dict)
        if jsonify:
            if pretty_print:
                return json.dumps(dict_out, indent=4)
            else:
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
    def create(cls, name, obj_class=None, *args, **kwargs):
        try:
            cls.get_by_name(name)
            raise DuplicateName('%s already exists with name "%s".' % (
                cls.__name__, name))
        except ValueError:
            pass
        if obj_class:
            obj = obj_class(name, *args, **kwargs)
        else:
            obj = cls(name, *args, **kwargs)
        return obj.save()

    @classmethod
    def get_by_name(cls, obj_name):
        obj = cls.query.filter(cls.name == obj_name).first()
        if not obj:
            raise ValueError('No %s found with name "%s".' % (cls.__name__,
                                                              obj_name))
        return obj

    @classmethod
    def delete_by_name(cls, obj_name):
        return cls.get_by_name(obj_name).delete()

    @classmethod
    def update_by_name(cls, obj_name, **kwargs):
        return cls.get_by_name(obj_name).update(**kwargs)

    @classmethod
    def get_by_id_or_name(cls, obj_id_or_name):
        obj_by_id = cls.query.filter(cls.id == obj_id_or_name).first()
        if obj_by_id:
            return obj_by_id
        obj_by_name = cls.query.filter(cls.name == obj_id_or_name).first()
        if obj_by_name:
            return obj_by_name
        raise ValueError('No %s found with id or name "%s".' % (cls.__name__,
                                                                obj_id_or_name))

    @classmethod
    def delete_by_id_or_name(cls, obj_id_or_name):
        return cls.get_by_id_or_name(obj_id_or_name).delete()

    @classmethod
    def update_by_id_or_name(cls, obj_id_or_name, **kwargs):
        return cls.get_by_id_or_name(obj_id_or_name).update(**kwargs)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)
