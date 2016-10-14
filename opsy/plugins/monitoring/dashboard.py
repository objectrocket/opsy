import uuid
from opsy.db import db, TimeStampMixin
from opsy.utils import parse_include_excludes


class Dashboard(TimeStampMixin, db.Model):

    __tablename__ = 'monitoring_dashboards'

    id = db.Column(db.String(36),  # pylint: disable=invalid-name
                   default=lambda: str(uuid.uuid4()), primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(256))
    enabled = db.Column('enabled', db.Boolean(), default=0)

    __table_args__ = (
        db.UniqueConstraint('name'),
    )

    filters = db.relationship('DashboardFilter', backref='dashboard',
                              lazy='dynamic')

    def __init__(self, name, description=None, enabled=0):
        self.name = name
        self.description = description
        self.enabled = enabled

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

    @classmethod
    def create_dashboard(cls, name, **kwargs):
        dashboard = cls(name, **kwargs)
        db.session.add(dashboard)
        db.session.commit()
        return dashboard

    @classmethod
    def get_dashboard_by_id(cls, dashboard_id):
        return cls.query.filter(cls.id == dashboard_id).first()

    @classmethod
    def get_dashboard_by_name(cls, name):
        return cls.query.filter(cls.name == name).first()

    @classmethod
    def get_dashboards(cls):
        return cls.query.all()

    @classmethod
    def delete_dashboard(cls, dashboard_id):
        cls.query.filter(cls.id == dashboard_id).delete()
        db.session.commit()

    @classmethod
    def update_dashboard(cls, dashboard_id, **kwargs):
        dashboard = cls.get_dashboard_by_id(dashboard_id)
        for k, v in kwargs.items():
            setattr(dashboard, k, v)
        db.session.commit()
        return dashboard

    def get_filters(self):
        filter_list = [DashboardFilter.dashboard_id == self.id]
        return DashboardFilter.query.filter(*filter_list).all()

    def get_filter_by_entity(self, entity_name):
        filter_list = [DashboardFilter.dashboard_id == self.id]
        filter_list.append(DashboardFilter.entity == entity_name)
        return DashboardFilter.query.filter(*filter_list).first()

    def create_filter(self, entity_name, filters):
        db.session.add(DashboardFilter(self.id, entity_name, filters))
        db.session.commit()

    def delete_filter(self, entity_name):
        DashboardFilter.query.filter(
            DashboardFilter.dashboard_id == self.id,
            DashboardFilter.entity == entity_name).delete()
        db.session.commit()

    def update_filter(self, entity_name, filters):
        filter_object = self.get_filter(entity)
        if filter_object:
            filter_object.update_filters(filters)
        else:
            filter_object = self.create_filter(entity, filters)
            db.session.add(filter_object)
        db.session.commit()

    def get_filters_list(self, entity):
        filters_list = []
        filters = self.get_filters()
        for map_entity, map_column in entity.get_filters_maps():
            for filter_object in filters:
                if filter_object.entity == map_entity:
                    includes, excludes = parse_include_excludes(
                        filter_object.filters)
                    if includes:
                        filters_list.append(map_column.in_(includes))
                    if excludes:
                        filters_list.append(~map_column.in_(excludes))
        return filters_list


class DashboardFilter(TimeStampMixin, db.Model):

    __tablename__ = 'monitoring_dashboards_filters'

    id = db.Column(db.String(36),  # pylint: disable=invalid-name
                   default=lambda: str(uuid.uuid4()), primary_key=True)
    dashboard_id = db.Column(db.String(36))
    entity = db.Column(db.String(16))
    filters = db.Column(db.String(256))

    __table_args__ = (
        db.ForeignKeyConstraint(['dashboard_id'], ['monitoring_dashboards.id'],
                                ondelete='CASCADE'),
        db.CheckConstraint(entity.in_(['dashboard', 'client', 'check'])),
        db.UniqueConstraint('dashboard_id', 'entity')
    )

    def __init__(self, dashboard_id, entity, filters):
        self.dashboard_id = dashboard_id
        self.entity = entity
        self.filters = filters

    def __repr__(self):
        return '<%s %s %s>' % (self.id, self.entity, self.filters)
