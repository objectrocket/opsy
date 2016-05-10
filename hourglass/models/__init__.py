from flask.ext.sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class TimeStampMixin(object):
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(),
                           onupdate=db.func.now())
