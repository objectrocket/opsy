from opsy.access import OpsyNeed, OpsyPermission


needs = {  # pylint: disable=invalid-name
    # Dashboards
    'dashboards_read': OpsyNeed('dashboards_read',
                                'Ability to list/show dashboards in the API.'),
    # Zones
    'zones_read': OpsyNeed('zones_read',
                           'Ability to list/show zones in the API.'),
    # Events
    'events_read': OpsyNeed('events_read',
                            'Ability to list/show events in the API.'),
    # Checks
    'checks_read': OpsyNeed('checks_read',
                            'Ability to list/show checks in the API.'),
    # Results
    'results_read': OpsyNeed('results_read',
                             'Ability to list/show results in the API.'),
    # Silences
    'silences_read': OpsyNeed('silences_read',
                              'Ability to list/show silences in the API.'),
    # Clients
    'clients_read': OpsyNeed('clients_read',
                             'Ability to list/show clients in the API.')
}

permissions = {  # pylint: disable=invalid-name
    # Dashboards
    'dashboards_read': OpsyPermission(needs.get('dashboards_read')),
    # Zones
    'zones_read': OpsyPermission(needs.get('zones_read')),
    # Events
    'events_read': OpsyPermission(needs.get('events_read')),
    # Checks
    'checks_read': OpsyPermission(needs.get('checks_read')),
    # Results
    'results_read': OpsyPermission(needs.get('results_read')),
    # Silences
    'silences_read': OpsyPermission(needs.get('silences_read')),
    # Clients
    'clients_read': OpsyPermission(needs.get('clients_read'))
}
