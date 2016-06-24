from time import time
from . import api
from hourglass.backends import db
from hourglass.utils import get_filters_list
from hourglass.backends.cache import *
from flask import current_app, jsonify, request


@api.route('/ping')
def ping():
    return jsonify({'pong': time()})


@api.route('/list/zones')
def list_zones():
    dashboard = request.args.get('dashboard')
    if dashboard:
        config = current_app.config
        dash_filters_list = Zone.get_dashboard_filters_list(config, dashboard)
        zones = [x[0] for x in Zone.query.filter(
            *dash_filters_list).with_entities(Zone.name).all()]
    else:
        zones = [x[0] for x in Zone.query.with_entities(Zone.name).all()]
    return jsonify({'zones': zones, 'timestamp': time()})


@api.route('/list/checks')
def list_checks():
    dashboard = request.args.get('dashboard')
    if dashboard:
        config = current_app.config
        dash_filters_list = Event.get_dashboard_filters_list(config, dashboard)
        events_query = Event.query.filter(*dash_filters_list)
    else:
        events_query = Event.query
    event_checks = [x[0] for x in events_query.with_entities(
        Event.check_name).distinct().all()]
    return jsonify({'checks': event_checks, 'timestamp': time()})


@api.route('/zones')
def zones():
    dashboard = request.args.get('dashboard')
    if dashboard:
        config = current_app.config
        dash_filters_list = Zone.get_dashboard_filters_list(config, dashboard)
        zones = Zone.query.filter(*dash_filters_list).all()
    else:
        zones = Zone.query.filter().all()
    zones = [x.dict_out for x in zones]
    return jsonify({'zones': zones, 'timestamp': time()})


@api.route('/zones/<zone_name>')
def zone(zone_name):
    zone = Zone.query.filter(Zone.name == zone_name).first()
    return jsonify({'zone': zone._dict_out(), 'timestamp': time()})


@api.route('/events')
def events():
    # TOO DO - change args from checkname/clientname to check_name/client_name
    dashboard = request.args.get('dashboard')
    hide_silenced = request.args.get('hide_silenced') or ''
    zones = request.args.get('zone')
    checks = request.args.get('check')
    clients = request.args.get('client')
    statuses = request.args.get('status')
    filters = ((zones, Event.zone_name),
               (checks, Event.check_name),
               (clients, Event.client_name),
               (statuses, Event.status))
    filters_list = get_filters_list(filters)
    hide_silenced = hide_silenced.split(',')
    if 'checks' in hide_silenced:
        filters_list.append(db.not_(Event.stash.any(
            client_name=Event.client_name, check_name=Event.check_name,
            flavor='silence')))
    if 'clients' in hide_silenced:
        filters_list.append(db.not_(Client.stash.any(
            client_name=Event.client_name, check_name='', flavor='silence')))
    if 'occurrences' in hide_silenced:
        filters_list.append(db.not_(
            Event.event_occurrences < Event.check_occurrences))
    if dashboard:
        config = current_app.config
        dash_filters_list = Event.get_dashboard_filters_list(config, dashboard)
        events_query = Event.query.filter(*dash_filters_list)
    else:
        events_query = Event.query
    events = events_query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'events': events, 'timestamp': time()})


@api.route('/checks')
def checks():
    dashboard = request.args.get('dashboard')
    zones = request.args.get('zone')
    checks = request.args.get('check')
    filters = ((zones, Check.zone_name),
               (checks, Check.name))
    filters_list = get_filters_list(filters)
    if dashboard:
        config = current_app.config
        dash_filters_list = Check.get_dashboard_filters_list(config, dashboard)
        checks_query = Check.query.filter(*dash_filters_list)
    else:
        checks_query = Check.query
    checks = checks_query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'checks': checks, 'timestamp': time()})


@api.route('/clients')
def clients():
    dashboard = request.args.get('dashboard')
    zones = request.args.get('zone')
    clients = request.args.get('client')
    filters = ((zones, Client.zone_name),
               (clients, Client.name))
    filters_list = get_filters_list(filters)
    if dashboard:
        config = current_app.config
        dash_filters_list = Client.get_dashboard_filters_list(config, dashboard)
        clients_query = Client.query.filter(*dash_filters_list)
    else:
        clients_query = Client.query
    clients = clients_query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'clients': clients, 'timestamp': time()})


@api.route('/clients/<zone>/<client>')
def client(zone, client):
    filters = ((zone, Client.zone_name),
               (client, Client.name))
    filters_list = get_filters_list(filters)
    clients = Client.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'clients': clients, 'timestamp': time()})


@api.route('/clients/<zone>/<client>/events')
def client_events(zone, client):
    filters = ((zone, Event.zone_name),
               (client, Event.client_name))
    filters_list = get_filters_list(filters)
    events = Event.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'events': events, 'timestamp': time()})


@api.route('/clients/<zone>/<client>/events/<check>')
def client_events_check(zone, client, check):
    filters = ((zone, Event.zone_name),
               (client, Event.client_name),
               (check, Event.check_name))
    filters_list = get_filters_list(filters)
    events = Event.query.filter(*filters_list).all_extra_as_dict()
    response = jsonify({'events': events, 'timestamp': time()})
    if not events:
        response.status_code = 404
    return response


@api.route('/clients/<zone>/<client>/results')
def client_results(zone, client):
    filters = ((zone, Result.zone_name),
               (client, Result.client_name))
    filters_list = get_filters_list(filters)
    results = Result.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'results': results, 'timestamp': time()})


@api.route('/clients/<zone>/<client>/results/<check>')
def client_results_check(zone, client, check):
    filters = ((zone, Result.zone_name),
               (client, Result.client_name),
               (check, Result.check_name))
    filters_list = get_filters_list(filters)
    results = Result.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'results': results, 'timestamp': time()})


@api.route('/clients/<zone>/<client>/stashes')
def client_stashes(zone, client):
    filters = ((zone, Stash.zone_name),
               (client, Stash.client_name))
    filters_list = get_filters_list(filters)
    stashes = Stash.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'stashes': stashes, 'timestamp': time()})


@api.route('/results')
def results():
    dashboard = request.args.get('dashboard')
    zones = request.args.get('zone')
    checks = request.args.get('check')
    clients = request.args.get('client')
    statuses = request.args.get('status')
    filters = ((zones, Result.zone_name),
               (checks, Result.check_name),
               (clients, Result.client_name),
               (statuses, Result.status))
    filters_list = get_filters_list(filters)
    if dashboard:
        config = current_app.config
        dash_filters_list = Result.get_dashboard_filters_list(config, dashboard)
        results_query = Result.query.filter(*dash_filters_list)
    else:
        results_query = Result.query
    results = results_query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'results': results, 'timestamp': time()})


@api.route('/stashes')
def stashes():
    zones = request.args.get('zone')
    clients = request.args.get('client')
    checks = request.args.get('check')
    flavor = request.args.get('flavor')
    filters = ((zones, Stash.zone_name),
               (clients, Stash.client_name),
               (checks, Stash.check_name),
               (flavor, Stash.flavor))
    filters_list = get_filters_list(filters)
    stashes = Stash.query.filter(*filters_list).all_extra_as_dict()
    return jsonify({'stashes': stashes, 'timestamp': time()})
