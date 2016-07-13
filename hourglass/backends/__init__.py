from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery
from flask import abort


db = SQLAlchemy()  # pylint: disable=invalid-name


class ExtraOut(BaseQuery):

    def all_dict_out(self):
        return [x.dict_out for x in self]

    def all_dict_extra_out(self):
        return [x.dict_extra_out for x in self]

    def all_dict_out_or_404(self):
        dict_list = self.all_dict_out()
        if not dict_list:
            abort(404)
        return dict_list

    def all_dict_extra_out_or_404(self):
        dict_list = self.all_dict_extra_out()
        if not dict_list:
            abort(404)
        return dict_list


class Silence(ExtraOut):

    def blah(self):
        pass


class BaseMetadata(db.Model):

    __bind_key__ = 'cache'
    __tablename__ = 'metadata'

    zone_name = db.Column(db.String(64), primary_key=True)
    entity = db.Column(db.String(64), primary_key=True)
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(64))
    updated_at = db.Column(db.DateTime, default=db.func.now(),
                           onupdate=db.func.now())

    __table_args__ = (
        db.ForeignKeyConstraint(['zone_name'], ['zones.name']),
    )

    def __init__(self, zone_name, key, entity, value):
        self.zone_name = zone_name
        self.key = key
        self.entity = entity
        self.value = value

    def __repr__(self):
        return '<%s %s: %s - %s>' % (self.__class__.__name__, self.zone_name,
                                     self.key, self.value)


class CacheBase(object):  # pylint: disable=too-few-public-methods

    metadata_class = BaseMetadata
    query_class = ExtraOut
    extra = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=db.func.now(),
                           onupdate=db.func.now())
    backend = db.Column(db.String(20))

    __mapper_args__ = {
        'polymorphic_on': backend,
        'polymorphic_identity': 'base'
    }

    @property
    def dict_extra_out(self):
        event_dict = self.dict_out
        event_dict['extra'] = self.extra
        return event_dict

    @classmethod
    def filter_api_response(cls, response):
        raise NotImplementedError

    @classmethod
    def last_poll_status(cls, zone_name):
        last_run = cls.metadata_class.query.filter(
            cls.metadata_class.key == 'update_status',
            cls.metadata_class.entity == cls.__tablename__,
            cls.metadata_class.zone_name == zone_name).first()
        return (last_run.updated_at, last_run.value)

    @classmethod
    def update_last_poll_status(cls, zone_name, status):
        cls.metadata_class.query.filter(
            cls.metadata_class.key == 'update_status',
            cls.metadata_class.entity == cls.__tablename__,
            cls.metadata_class.zone_name == zone_name).delete()
        return cls.metadata_class(zone_name, 'update_status',
                                  cls.__tablename__, status)
