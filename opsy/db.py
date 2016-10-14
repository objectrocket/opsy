from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()  # pylint: disable=invalid-name


class TimeStampMixin(object):
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(),
                           onupdate=db.func.now())
