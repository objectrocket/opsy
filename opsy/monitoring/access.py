from functools import partial
from opsy.access import Need


MonitoringNeed = partial(Need, 'monitoring')  # pylint: disable=invalid-name

# Dashboards
DASHBOARDS_CREATE = MonitoringNeed(
    'dashboards_create', 'Ability to list/show dashboards in the API.')
DASHBOARDS_READ = MonitoringNeed(
    'dashboards_read', 'Ability to list/show dashboards in the API.')
DASHBOARDS_UPDATE = MonitoringNeed(
    'dashboards_update', 'Ability to list/show dashboards in the API.')
DASHBOARDS_DELETE = MonitoringNeed(
    'dashboards_delete', 'Ability to list/show dashboards in the API.')
# Monitoring Services
MONITORING_SERVICE_CREATE = MonitoringNeed(
    'monitoring_services_create', 'Ability to list/show zones in the API.')
MONITORING_SERVICE_READ = MonitoringNeed(
    'monitoring_services_read', 'Ability to list/show zones in the API.')
MONITORING_SERVICE_UPDATE = MonitoringNeed(
    'monitoring_services_update', 'Ability to list/show zones in the API.')
MONITORING_SERVICE_DELETE = MonitoringNeed(
    'monitoring_services_delete', 'Ability to list/show zones in the API.')
# Events
EVENTS_CREATE = MonitoringNeed(
    'events_create', 'Ability to list/show events in the API.')
EVENTS_READ = MonitoringNeed(
    'events_read', 'Ability to list/show events in the API.')
EVENTS_UPDATE = MonitoringNeed(
    'events_update', 'Ability to list/show events in the API.')
EVENTS_DELETE = MonitoringNeed(
    'events_delete', 'Ability to list/show events in the API.')

MONITORING_NEEDS = [
    DASHBOARDS_CREATE, DASHBOARDS_READ, DASHBOARDS_UPDATE, DASHBOARDS_DELETE,
    MONITORING_SERVICE_CREATE, MONITORING_SERVICE_READ,
    MONITORING_SERVICE_UPDATE, MONITORING_SERVICE_DELETE,
    EVENTS_CREATE, EVENTS_READ, EVENTS_UPDATE, EVENTS_DELETE,
]
