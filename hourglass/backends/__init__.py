from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery
from flask import json


db = SQLAlchemy()  # pylint: disable=invalid-name


class ExtraOut(BaseQuery):

    def all_extra_as_dict(self):
        return [json.loads(x.extra) for x in self]

    def all_extra_as_json(self):
        return json.dumps(self.all_extra_as_dict())


class CacheBase(object):  # pylint: disable=too-few-public-methods
    query_class = ExtraOut
    extra = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=db.func.now(),
                           onupdate=db.func.now())
    backend = db.Column(db.String(20))

    __mapper_args__ = {
        'polymorphic_on': backend,
        'polymorphic_identity': 'base'
    }
