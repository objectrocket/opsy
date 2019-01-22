from functools import partial
from opsy.access import Need


MonitoringNeed = partial(Need, 'monitoring')  # pylint: disable=invalid-name

# Dashboards
DASHBOARDS_READ = MonitoringNeed(
    'dashboards_read', 'Ability to list/show dashboards in the API.')
# Zones
ZONES_READ = MonitoringNeed(
    'zones_read', 'Ability to list/show zones in the API.')
# Events
EVENTS_READ = MonitoringNeed(
    'events_read', 'Ability to list/show events in the API.')
# Checks
CHECKS_READ = MonitoringNeed(
    'checks_read', 'Ability to list/show checks in the API.')
# Results
RESULTS_READ = MonitoringNeed(
    'results_read', 'Ability to list/show results in the API.')
# Silences
SILENCES_READ = MonitoringNeed(
    'silences_read', 'Ability to list/show silences in the API.')
# Clients
CLIENTS_READ = MonitoringNeed(
    'clients_read', 'Ability to list/show clients in the API.')

MONITORING_NEEDS = [
    DASHBOARDS_READ, ZONES_READ, EVENTS_READ, CHECKS_READ, RESULTS_READ,
    SILENCES_READ, CLIENTS_READ
]
