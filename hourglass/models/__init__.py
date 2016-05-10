from flask.ext.sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class HourglassMixin(object):
    updated_at = db.Column(db.DateTime, default=db.func.now(),
                           onupdate=db.func.now())
