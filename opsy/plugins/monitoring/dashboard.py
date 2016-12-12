from opsy.db import db, TimeStampMixin, DictOut, IDedResource, NamedResource
from opsy.utils import parse_include_excludes


class Dashboard(IDedResource, NamedResource, TimeStampMixin, db.Model):

    __tablename__ = 'monitoring_dashboards'

    query_class = DictOut

    description = db.Column(db.String(256))
    enabled = db.Column('enabled', db.Boolean(), default=0)

    filters = db.relationship('DashboardFilter', backref='dashboard',
                              lazy='dynamic', query_class=DictOut)

    def __init__(self, name, description=None, enabled=0):
        self.name = name
        self.description = description
        self.enabled = enabled

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

    @classmethod
    def create_dashboard(cls, name, description=None, enabled=0,
                         zone_filters=None, client_filters=None,
                         check_filters=None):
        dashboard = cls(name, description=description, enabled=enabled)
        db.session.add(dashboard)  # pylint: disable=no-member
        db.session.commit()
        if zone_filters:
            dashboard.create_filter('zone', zone_filters)
        if client_filters:
            dashboard.create_filter('client', client_filters)
        if check_filters:
            dashboard.create_filter('check', check_filters)
        return dashboard

    @classmethod
    def delete_dashboard(cls, dashboard_id):
        cls.query.filter(cls.id == dashboard_id).delete()
        db.session.commit()

    @classmethod
    def update_dashboard(cls, dashboard_id, **kwargs):
        dashboard = cls.get_by_id(dashboard_id)
        for key, value in kwargs.items():
            setattr(dashboard, key, value)
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
        db.session.add(DashboardFilter(self.id, entity_name, filters))  # pylint: disable=no-member
        db.session.commit()

    def delete_filter(self, entity_name):
        DashboardFilter.query.filter(
            DashboardFilter.dashboard_id == self.id,
            DashboardFilter.entity == entity_name).delete()
        db.session.commit()

    def update_filter(self, entity_name, filters):
        filter_object = self.get_filter_by_entity(entity_name)
        if filter_object:
            filter_object.filters = filters
        else:
            filter_object = self.create_filter(entity_name, filters)
            db.session.add(filter_object)  # pylint: disable=no-member
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

    @property
    def dict_out(self):
        filters_dict = self.filters.all_dict_out()
        return {
            'id': self.id,
            'name': self.name,
            'updated_at': self.updated_at,
            'created_at': self.created_at,
            'description': self.description,
            'enabled': self.enabled,
            'filters': filters_dict
        }


class DashboardFilter(IDedResource, TimeStampMixin, db.Model):

    __tablename__ = 'monitoring_dashboards_filters'

    query_class = DictOut

    dashboard_id = db.Column(db.String(36))
    entity = db.Column(db.String(16))
    filters = db.Column(db.String(256))

    __table_args__ = (
        db.ForeignKeyConstraint(['dashboard_id'], ['monitoring_dashboards.id'],
                                ondelete='CASCADE'),
        db.CheckConstraint(entity.in_(['zone', 'client', 'check'])),
        db.UniqueConstraint('dashboard_id', 'entity')
    )

    def __init__(self, dashboard_id, entity, filters):
        self.dashboard_id = dashboard_id
        self.entity = entity
        self.filters = filters

    @property
    def dict_out(self):
        return {
            'id': self.id,
            'dashboard_id': self.dashboard_id,
            'updated_at': self.updated_at,
            'created_at': self.created_at,
            'entity': self.entity,
            'filters': self.filters,
        }

    def __repr__(self):
        return '<%s %s %s>' % (self.id, self.entity, self.filters)
