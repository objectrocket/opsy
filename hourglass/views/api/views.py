from time import time
from . import api
from hourglass.models.backends import db
from hourglass.models.backends.sensu.cache import Event, Check, Client, Stash
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
    checknames = config['dashboards'][dashboard].get('checkname')
    clientnames = config['dashboards'][dashboard].get('clientname')
    statuses = config['dashboards'][dashboard].get('status')
    filters = ((datacenters, Event.datacenter),
               (checknames, Event.checkname),
               (clientnames, Event.clientname),
               (statuses, Event.status))
    return get_filters_list(filters)


@api.route('/ping')
def ping():
    return jsonify({'pong': time()})


@api.route('/list/datacenters')
def list_datacenters():
    dashboard = request.args.get('dashboard')
    config = current_app.config
    datacenters = [x for x in config['sensu_nodes'].keys()]
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
    eventchecks = [x[0] for x in events_query.with_entities(
        Event.checkname).distinct().all()]
    return jsonify({'checks': eventchecks, 'timestamp': time()})


@api.route('/events')
def events():
    dashboard = request.args.get('dashboard')
    hide_silenced = request.args.get('hide_silenced') or ''
    datacenters = request.args.get('datacenter')
    checknames = request.args.get('checkname')
    clientnames = request.args.get('clientname')
    statuses = request.args.get('status')
    filters = ((datacenters, Event.datacenter),
               (checknames, Event.checkname),
               (clientnames, Event.clientname),
               (statuses, Event.status))
    filters_list = get_filters_list(filters)
    hide_silenced = hide_silenced.split(',')
    if 'checks' in hide_silenced:
        filters_list.append(db.not_(Event.stash.has(
            clientname=Event.clientname, checkname=Event.checkname,
            flavor='silence')))
    if 'clients' in hide_silenced:
        filters_list.append(db.not_(Client.stash.has(
            clientname=Event.clientname, checkname=None,
            flavor='silence')))
    if 'occurrences' in hide_silenced:
        filters_list.append(db.not_(
            Event.eventoccurrences < Event.checkoccurrences))
    if dashboard:
        config = current_app.config
        dash_filters_list = get_dashboard_filters_list(config, dashboard)
        events_query = Event.query.filter(*dash_filters_list)
    else:
        events_query = Event.query
    sensuevents = events_query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'events': sensuevents, 'timestamp': time()})


@api.route('/checks')
def checks():
    datacenters = request.args.get('datacenter')
    checknames = request.args.get('checkname')
    filters = ((datacenters, Check.datacenter),
               (checknames, Check.name))
    filters_list = get_filters_list(filters)
    sensuchecks = Check.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'checks': sensuchecks, 'timestamp': time()})


@api.route('/clients')
def clients():
    datacenters = request.args.get('datacenter')
    clientnames = request.args.get('clientname')
    filters = ((datacenters, Client.datacenter),
               (clientnames, Client.name))
    filters_list = get_filters_list(filters)
    sensuclients = Client.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'clients': sensuclients, 'timestamp': time()})


@api.route('/stashes')
def stashes():
    datacenters = request.args.get('datacenter')
    clientnames = request.args.get('clientname')
    checknames = request.args.get('checkname')
    flavor = request.args.get('flavor')
    filters = ((datacenters, Stash.datacenter),
               (clientnames, Stash.clientname),
               (checknames, Stash.checkname),
               (flavor, Stash.flavor))
    filters_list = get_filters_list(filters)
    sensustashes = Stash.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'stashes': sensustashes, 'timestamp': time()})
