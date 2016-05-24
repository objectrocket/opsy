from time import time
from . import api
from hourglass.models.backends import db
from hourglass.models.backends.sensu.cache import *
from flask import current_app, jsonify, request


def get_filters_list(filters):
    filters_list = []
    for items, db_object in filters:
        if items:
            include, exclude = parse_include_excludes(items)
            if include:
                filters_list.append(db_object.in_(include))
            if exclude:
                filters_list.append(~db_object.in_(exclude))
    return filters_list


def parse_include_excludes(items):
    if items:
        item_list = items.split(',')
        # Wrap in a set to remove duplicates
        include = list(set([x for x in item_list if not x.startswith('!')]))
        exclude = list(set([x[1:] for x in item_list if x.startswith('!')]))
    else:
        include, exclude = [], []
    return include, exclude


def get_dashboard_filters_list(config, dashboard):
    datacenters = config['dashboards'][dashboard].get('datacenter')
    check_names = config['dashboards'][dashboard].get('check_name')
    client_names = config['dashboards'][dashboard].get('client_name')
    statuses = config['dashboards'][dashboard].get('status')
    filters = ((datacenters, Event.datacenter),
               (check_names, Event.check_name),
               (client_names, Event.client_name),
               (statuses, Event.status))
    return get_filters_list(filters)


@api.route('/ping')
def ping():
    return jsonify({'pong': time()})


@api.route('/list/datacenters')
def list_datacenters():
    dashboard = request.args.get('dashboard')
    config = current_app.config
    datacenters = [x for x in config['sensu_nodes']]
    if dashboard:
        datacenters_string = config['dashboards'][dashboard].get('datacenter')
        include, exclude = parse_include_excludes(datacenters_string)
        if include:
            datacenters = include
        if exclude:
            datacenters = list(set(datacenters) - set(exclude))
    return jsonify({'datacenters': datacenters, 'timestamp': time()})


@api.route('/list/checks')
def list_checks():
    dashboard = request.args.get('dashboard')
    if dashboard:
        config = current_app.config
        dash_filters_list = get_dashboard_filters_list(config, dashboard)
        events_query = Event.query.filter(*dash_filters_list)
    else:
        events_query = Event.query
    event_checks = [x[0] for x in events_query.with_entities(
        Event.check_name).distinct().all()]
    return jsonify({'checks': event_checks, 'timestamp': time()})


@api.route('/events')
def events():
    dashboard = request.args.get('dashboard')
    hide_silenced = request.args.get('hide_silenced') or ''
    datacenters = request.args.get('datacenter')
    check_names = request.args.get('check_name')
    client_names = request.args.get('client_name')
    statuses = request.args.get('status')
    filters = ((datacenters, Event.datacenter),
               (check_names, Event.check_name),
               (client_names, Event.client_name),
               (statuses, Event.status))
    filters_list = get_filters_list(filters)
    hide_silenced = hide_silenced.split(',')
    if 'checks' in hide_silenced:
        filters_list.append(db.not_(Event.stash.has(
            client_name=Event.client_name, check_name=Event.check_name,
            flavor='silence')))
    if 'clients' in hide_silenced:
        filters_list.append(db.not_(Client.stash.has(
            client_name=Event.client_name, check_name=None,
            flavor='silence')))
    if 'occurrences' in hide_silenced:
        filters_list.append(db.not_(
            Event.event_occurrences < Event.check_occurrences))
    if dashboard:
        config = current_app.config
        dash_filters_list = get_dashboard_filters_list(config, dashboard)
        events_query = Event.query.filter(*dash_filters_list)
    else:
        events_query = Event.query
    sensu_events = events_query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'events': sensu_events, 'timestamp': time()})


@api.route('/checks')
def checks():
    datacenters = request.args.get('datacenter')
    check_names = request.args.get('check_name')
    filters = ((datacenters, Check.datacenter),
               (check_names, Check.name))
    filters_list = get_filters_list(filters)
    sensu_checks = Check.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'checks': sensu_checks, 'timestamp': time()})


@api.route('/clients')
def clients():
    datacenters = request.args.get('datacenter')
    client_names = request.args.get('client_name')
    filters = ((datacenters, Client.datacenter),
               (client_names, Client.name))
    filters_list = get_filters_list(filters)
    sensu_clients = Client.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'clients': sensu_clients, 'timestamp': time()})


@api.route('/results')
def results():
    datacenters = request.args.get('datacenter')
    check_names = request.args.get('check_name')
    client_names = request.args.get('client_name')
    statuses = request.args.get('status')
    filters = ((datacenters, Result.datacenter),
               (check_names, Result.check_name),
               (client_names, Result.client_name),
               (statuses, Result.status))
    filters_list = get_filters_list(filters)
    sensu_results = Result.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'results': sensu_results, 'timestamp': time()})


@api.route('/stashes')
def stashes():
    datacenters = request.args.get('datacenter')
    client_names = request.args.get('client_name')
    check_names = request.args.get('check_name')
    flavor = request.args.get('flavor')
    filters = ((datacenters, Stash.datacenter),
               (client_names, Stash.client_name),
               (check_names, Stash.check_name),
               (flavor, Stash.flavor))
    filters_list = get_filters_list(filters)
    sensu_stashes = Stash.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'stashes': sensu_stashes, 'timestamp': time()})
