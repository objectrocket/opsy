from marshmallow import RAISE
from marshmallow import fields as ma_fields
from marshmallow_sqlalchemy import field_for
from prettytable import PrettyTable
from opsy.schema import BaseSchema
from opsy.plugins.monitoring.backends.base import Client, Check, Result, \
    Event, Silence, Zone
from opsy.plugins.monitoring.dashboard import Dashboard, DashboardFilter


###############################################################################
# Sqlalchemy schemas
###############################################################################


class ClientSchema(BaseSchema):

    class Meta:
        model = Client
        fields = ('id', 'name', 'zone_name', 'zone_id', 'backend',
                  'subscriptions', 'silences', 'updated_at', 'last_poll_time')
        ordered = True
        unknown = RAISE

    last_poll_time = field_for(Zone, 'last_poll_time')

    silences = ma_fields.Nested('SilenceSchema', many=True, dump_only=True)


class CheckSchema(BaseSchema):

    class Meta:
        model = Check
        fields = ('id', 'name', 'zone_name', 'zone_id', 'backend',
                  'subscribers', 'occurrences_threshold', 'interval',
                  'command', 'last_poll_time', 'updated_at')
        ordered = True
        unknown = RAISE

    last_poll_time = field_for(Zone, 'last_poll_time')


class ResultSchema(BaseSchema):

    class Meta:
        model = Result
        fields = ('id', 'client_name', 'check_name', 'zone_name', 'zone_id',
                  'backend', 'check_subscribers', 'occurrences_threshold',
                  'status', 'interval', 'command', 'output', 'last_poll_time',
                  'updated_at', 'silences')
        ordered = True
        unknown = RAISE

    last_poll_time = field_for(Zone, 'last_poll_time')

    silences = ma_fields.Nested('SilenceSchema', many=True, dump_only=True)


class EventSchema(BaseSchema):

    class Meta:
        model = Event
        fields = ('id', 'client_name', 'check_name', 'zone_name', 'zone_id',
                  'backend', 'client_subscriptions', 'check_subscribers',
                  'occurrences_threshold', 'occurrences', 'status', 'interval',
                  'command', 'output', 'last_poll_time', 'updated_at',
                  'silences')
        ordered = True
        unknown = RAISE

    last_poll_time = field_for(Zone, 'last_poll_time')

    silences = ma_fields.Nested('SilenceSchema', many=True, dump_only=True)


class SilenceSchema(BaseSchema):

    class Meta:
        model = Silence
        fields = ('id', 'client_name', 'check_name', 'zone_name', 'zone_id',
                  'backend', 'subscription', 'creator', 'reason',
                  'last_poll_time', 'created_at', 'expire_at')
        ordered = True

    last_poll_time = field_for(Zone, 'last_poll_time')


class ZoneSchema(BaseSchema):

    class Meta:
        model = Zone
        fields = ('id', 'name', 'backend', 'status', 'status_message', 'host',
                  'path', 'protocol', 'port', 'timeout', 'interval', 'enabled',
                  'last_poll_time', 'created_at', 'updated_at')
        ordered = True

    enabled = field_for(Zone, '_enabled', field_class=ma_fields.Str)


class DashboardSchema(BaseSchema):

    class Meta:
        model = Dashboard
        fields = ('id', 'name', 'description', 'enabled', 'updated_at',
                  'created_at', 'filters')
        ordered = True

    filters = ma_fields.Nested(
        'DashboardFilterSchema', many=True, dump_only=True)

    def pt_dumps(self, obj, many=None):
        """Returns a prettytable representation of the data."""
        many = self.many if many is None else bool(many)
        data = self.dump(obj, many=many)
        if many:
            columns = []
            for attr_name, field_obj in self.fields.items():
                if getattr(field_obj, 'load_only', False):
                    continue
                if field_obj.data_key or attr_name == 'filters':
                    continue
                columns.append(field_obj.data_key or attr_name)
            table = PrettyTable(columns, align='l')
            for entity in data:
                table.add_row([entity.get(x) for x in columns])
            return_data = str(table)
        else:
            user_table = PrettyTable(['Property', 'Value'], align='l')
            filters = None
            for key, value in data.items():
                if key == 'filters':
                    filters = value
                    continue
                user_table.add_row([key, value])
            return_data = f'{user_table}\n\nFilters:'
            try:
                columns = filters[0].keys()
                filters_table = PrettyTable(columns, align='l')
                for setting in filters:
                    filters_table.add_row(setting.values())
                return_data = f'{return_data}\n{filters_table}'
            except IndexError:
                return_data = f'{return_data} No dashboard filters found.'
        return return_data


class DashboardFilterSchema(BaseSchema):

    class Meta:
        model = DashboardFilter
        fields = ('id', 'dashboard_id', 'entity', 'filters', 'created_at',
                  'updated_at')
        ordered = True
