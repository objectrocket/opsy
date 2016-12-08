import uuid
from datetime import datetime
from flask_sqlalchemy import BaseQuery, SQLAlchemy
from flask import abort


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

    @classmethod
    def get(cls, output_query=False, filters_list=None):
        query_obj = cls.query
        if filters_list:
            query_obj = query_obj.filter(*filters_list)
        if output_query:
            return query_obj
        return query_obj.all()

    @property
    def dict_out(self):
        return {}

    def get_dict(self, **kwargs):
        return self.dict_out


class IDedResource(BaseResource):

    id = db.Column(db.String(36),  # pylint: disable=invalid-name
                   default=lambda: str(uuid.uuid4()), primary_key=True)

    @classmethod
    def get_by_id(cls, obj_id):
        return cls.query.filter(cls.id == obj_id).first()


class NamedResource(BaseResource):

    name = db.Column(db.String(128), unique=True)

    @classmethod
    def get_by_name(cls, obj_name):
        return cls.query.filter(cls.name == obj_name).first()
