from time import time
from . import api
from hourglass.models.api import Event, Check, Client
from flask import jsonify, request


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


@api.route('/ping')
def ping():
    return jsonify({'pong': time()})


@api.route('/events')
def events():
    datacenters = request.args.get("datacenter")
    checknames = request.args.get("checkname")
    clientnames = request.args.get("clientname")
    filters = ((datacenters, Event.datacenter),
               (checknames, Event.checkname),
               (clientnames, Event.clientname))
    filters_list = get_filters_list(filters)
    sensuevents = Event.query.filter(*filters_list).all_extra_as_dict()
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
