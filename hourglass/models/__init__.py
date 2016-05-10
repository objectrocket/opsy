from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery


db = SQLAlchemy()


class JsonOut(BaseQuery):
    def as_json(self):
        return "this is a test"


class HourglassMixin(object):
    updated_at = db.Column(db.DateTime, default=db.func.now(),
                           onupdate=db.func.now())
    query_class = JsonOut
