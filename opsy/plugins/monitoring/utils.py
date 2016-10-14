from opsy.plugins.monitoring.backends.base import Client, Check, Result, \
    Event, Silence, Zone

ENTITY_MAP = {'client': Client, 'check': Check, 'result': Result,
              'event': Event, 'silence': Silence, 'zone': Zone}


class MonitoringFilter(object):

    def __init__(self, entity, filters):
        if entity not in ['zone', 'client', 'check']:
            raise ValueError('Entity must be zone, client, or check.')
        self.entity = entity
        self._parse_filter(filters)

    @property
    def entity_class(self):
        return ENTITY_MAP[self.entity]

    def get_filters_list(self):
        filters_list = []
        if self.includes:
            filters_list.append(self.entity_class.in_(self.includes))
        if self.excludes:
            filters_list.append(~self.entity_class.in_(self.excludes))
        return filters_list

    def _parse_filter(self, filters):
        self.includes, self.excludes = [], []
        if filters:
            filter_items = filters.split(',')
            # Wrap in a set to remove duplicates
            self.includes = list(
                set([x for x in filter_items if not x.startswith('!')]))
            self.excludes = list(
                set([x[1:] for x in filter_items if x.startswith('!')]))
