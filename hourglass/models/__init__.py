from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery
from flask import json


db = SQLAlchemy()


class JsonOut(BaseQuery):

    def all_extra_as_dict(self):
        out_list = []
        for x in self:
            out_list.append(json.loads(x.extra))
        return out_list

    def all_extra_as_json(self):
        return json.dumps(self.all_extra_as_dict())


class HourglassCacheMixin(object):
    query_class = JsonOut
    updated_at = db.Column(db.DateTime, default=db.func.now(),
                           onupdate=db.func.now())
