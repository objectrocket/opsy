from time import time
from . import api
from hourglass.models import db
from hourglass.models.api import Event, Check, Client
from flask import current_app, jsonify, request


def get_filters_list(filters):
    filters_list = []
    for items, db_object in filters:
        if items:
            item_list = items.split(',')
            include = [x for x in item_list if not x.startswith('!')]
            exclude = [x[1:] for x in item_list if x.startswith('!')]
            if include:
                filters_list.append(db_object.in_(include))
            if exclude:
                filters_list.append(~db_object.in_(exclude))
    return filters_list


def get_dashboard_filters_list(config, dashboard):
    datacenters = config['dashboards'][dashboard].get("datacenter")
    checknames = config['dashboards'][dashboard].get("checkname")
    clientnames = config['dashboards'][dashboard].get("clientname")
    statuses = config['dashboards'][dashboard].get("status")
    filters = ((datacenters, Event.datacenter),
               (checknames, Event.checkname),
               (clientnames, Event.clientname),
               (statuses, Event.status))
    return get_filters_list(filters)


@api.route('/ping')
def ping():
    return jsonify({'pong': time()})


@api.route('/events')
def events():
    dashboard = request.args.get("dashboard")
    hide_silenced = request.args.get("hide_silenced")
    datacenters = request.args.get("datacenter")
    checknames = request.args.get("checkname")
    clientnames = request.args.get("clientname")
    statuses = request.args.get("status")
    filters = ((datacenters, Event.datacenter),
               (checknames, Event.checkname),
               (clientnames, Event.clientname),
               (statuses, Event.status))
    filters_list = get_filters_list(filters)
    if hide_silenced == "1":
        filters_list.append(db.not_(Event.stash.has(
            clientname=Event.clientname, checkname=Event.checkname,
            flavor='silence')))
    if dashboard:
        config = current_app.config
        dash_filters_list = get_dashboard_filters_list(config, dashboard)
        events_query = Event.query.filter(*dash_filters_list)
    else:
        events_query = Event.query
    sensuevents = events_query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'events': sensuevents, 'timestamp': time()})


@api.route('/events/datacenters')
def events_datacenters():
    datacenters = [x[0] for x in Event.query.with_entities(Event.datacenter).distinct().all()]
    return jsonify({'datacenters': datacenters, 'timestamp': time()})


@api.route('/events/checks')
def events_checks():
    eventchecks = [x[0] for x in Event.query.with_entities(Event.checkname).distinct().all()]
    return jsonify({'checks': eventchecks, 'timestamp': time()})


@api.route('/checks')
def checks():
    datacenters = request.args.get("datacenter")
    checknames = request.args.get("checkname")
    filters = ((datacenters, Check.datacenter),
               (checknames, Check.name))
    filters_list = get_filters_list(filters)
    sensuchecks = Check.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'checks': sensuchecks, 'timestamp': time()})


@api.route('/clients')
def clients():
    datacenters = request.args.get("datacenter")
    clientnames = request.args.get("clientname")
    filters = ((datacenters, Client.datacenter),
               (clientnames, Client.name))
    filters_list = get_filters_list(filters)
    sensuclients = Client.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'clients': sensuclients, 'timestamp': time()})
