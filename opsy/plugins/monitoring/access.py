from opsy.auth.access import OpsyNeed, OpsyPermission


needs = {  # pylint: disable=invalid-name
    # Events
    'view_events': OpsyNeed('view_events',
                            'Ability to list/show events in the API.')
}

permissions = {  # pylint: disable=invalid-name
    # Users
    'view_events': OpsyPermission(needs.get('view_events')),
}
