from marshmallow import RAISE
from opsy.flask_extensions import ma
from opsy.schema import BaseSchema, Password
from opsy.monitoring.models import Dashboard, Event, MonitoringService


###############################################################################
# Non-sqlalchemy schemas
###############################################################################

class HttpPollerBackendSchema(BaseSchema):
    class Meta:
        fields = ('host', 'protocol', 'port', 'path', 'interval', 'timeout',
                  'username', 'password', 'verify_ssl')
        ordered = True
        unknown = RAISE

    host = ma.String()
    protocol = ma.String()
    port = ma.Integer()
    path = ma.String()
    interval = ma.Integer()
    timeout = ma.Integer()
    username = ma.String()
    password = Password()
    verify_ssl = ma.Boolean()

###############################################################################
# Sqlalchemy schemas
###############################################################################


class MonitoringServiceSchema(BaseSchema):

    class Meta:
        model = MonitoringService
        fields = ('id', 'name', 'zone_id', 'enabled',
                  'backend_config', 'backend_name', 'interval',
                  'last_poll_time', 'extra')
        ordered = True
        unknown = RAISE

    backend_config = ma.Nested('HttpPollerBackendSchema')


class EventSchema(BaseSchema):

    class Meta:
        model = Event
        fields = ('id', 'monitoring_service_id', 'monitoring_service_name',
                  'zone_name', 'assignee_name', 'host_id'
                  'host_name', 'check_name', 'state', 'status', 'interval',
                  'interval', 'occurrences', 'command', 'output', 'resolved',
                  'resolved_at', 'extra')
        ordered = True
        unknown = RAISE


class DashboardSchema(BaseSchema):

    class Meta:
        model = Dashboard
        fields = ('id', 'client_name', 'check_name', 'zone_name', 'zone_id',
                  'backend', 'client_subscriptions', 'check_subscribers',
                  'occurrences_threshold', 'occurrences', 'status', 'interval',
                  'command', 'output', 'last_poll_time', 'updated_at',
                  'silences')
        ordered = True
        unknown = RAISE
