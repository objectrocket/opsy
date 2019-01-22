from prettytable import PrettyTable
from opsy.models import TimeStampMixin, OpsyQuery, BaseResource, NamedResource
from opsy.flask_extensions import db
from opsy.utils import parse_include_excludes
from opsy.exceptions import DuplicateError


class Dashboard(NamedResource, TimeStampMixin, db.Model):

    __tablename__ = 'monitoring_dashboards'

    query_class = OpsyQuery

    description = db.Column(db.String(256))
    enabled = db.Column('enabled', db.Boolean(), default=0)

    filters = db.relationship('DashboardFilter', backref='dashboard',
                              lazy='dynamic', query_class=OpsyQuery)

    @classmethod
    def create(cls, name, description=None, enabled=0, zone_filters=None,
               client_filters=None, check_filters=None):
        dashboard = super().create(name, description=description,
                                   enabled=enabled)
        if zone_filters:
            dashboard.create_filter('zone', zone_filters)  # pylint: disable=no-member
        if client_filters:
            dashboard.create_filter('client', client_filters)  # pylint: disable=no-member
        if check_filters:
            dashboard.create_filter('check', check_filters)  # pylint: disable=no-member
        return dashboard

    def pretty_print(self, all_attrs=False, ignore_attrs=None):
        super().pretty_print(all_attrs=all_attrs, ignore_attrs=ignore_attrs)
        print('\nFilters:')
        columns = ['id', 'entity', 'filters', 'created_at', 'updated_at']
        table = PrettyTable(columns)
        for filter_object in self.get_filters():
            filter_object_dict = filter_object.get_dict(all_attrs=True)
            table.add_row([filter_object_dict.get(x) for x in columns])
        print(table)

    def update(self, **kwargs):
        if kwargs.get('zone_filters'):
            self.update_filter('zone', kwargs['zone_filters'])
            del kwargs['zone_filters']
        if kwargs.get('client_filters'):
            self.update_filter('client', kwargs['client_filters'])
            del kwargs['client_filters']
        if kwargs.get('check_filters'):
            self.update_filter('check', kwargs['check_filters'])
            del kwargs['check_filters']
        return super().update(**kwargs)

    def get_filters(self):
        filter_list = [DashboardFilter.dashboard_id == self.id]
        return DashboardFilter.query.filter(*filter_list).all()

    def get_filter_by_entity(self, entity_name):
        obj = DashboardFilter.query.filter(
            DashboardFilter.dashboard_id == self.id,
            DashboardFilter.entity == entity_name).first()
        return obj

    def create_filter(self, entity_name, filters):
        if self.get_filter_by_entity(entity_name):
            raise DuplicateError('Filter already exists for entity "%s".'
                                 % (entity_name))
        return DashboardFilter(self.id, entity_name, filters).save()

    def delete_filter(self, entity_name):
        return self.get_filter_by_entity(entity_name).delete()

    def update_filter(self, entity_name, filters):
        try:
            filter_object = self.get_filter_by_entity(entity_name)
            return filter_object.update(filters=filters)
        except AttributeError:
            return self.create_filter(entity_name, filters).save()

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

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)


class DashboardFilter(BaseResource, TimeStampMixin, db.Model):

    __tablename__ = 'monitoring_dashboards_filters'

    query_class = OpsyQuery

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
        super().__init__(dashboard_id=dashboard_id, entity=entity,
                         filters=filters)

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
