from . import api
from hourglass import db
from hourglass.utils import get_filters_list
from hourglass.backends.cache import Client, Check, Result, Event, Silence, \
    Zone
from flask import current_app, jsonify, request


@api.route('/zones')
def zones():
    dashboard = request.args.get('dashboard')
    if dashboard:
        config = current_app.config
        dash_filters_list = Zone.get_dashboard_filters_list(config, dashboard)
        zones = Zone.query.filter(*dash_filters_list).all_dict_out_or_404()
    else:
        zones = Zone.query.filter().all_dict_out_or_404()
    return jsonify({'zones': zones})


@api.route('/zones/<zone_name>')
def zone(zone_name):
    zone = Zone.query.filter(Zone.name == zone_name).all_dict_out_or_404()
    return jsonify({'zone': zone})


@api.route('/events')
def events():
    dashboard = request.args.get('dashboard')
    try:
        count_checks = request.args['count_checks']
        count_checks = True
    except:
        count_checks = False
    hide_silenced = request.args.get('hide_silenced', '')
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
        filters_list.append(db.not_(Event.silences.any(
            client_name=Event.client_name, check_name=Event.check_name)))
    if 'clients' in hide_silenced:
        filters_list.append(db.not_(Client.silences.any(
            client_name=Event.client_name, check_name='')))
    if 'occurrences' in hide_silenced:
        filters_list.append(db.not_(
            Event.event_occurrences < Event.check_occurrences))
    if dashboard:
        config = current_app.config
        dash_filters_list = Event.get_dashboard_filters_list(config, dashboard)
        events_query = Event.query.filter(*dash_filters_list)
    else:
        events_query = Event.query
    if count_checks:
        events = {x: y for x, y in events_query.with_entities(
            Event.check_name, db.func.count(Event.check_name)).filter(
            *filters_list).group_by(
            Event.check_name).order_by(db.desc(db.func.count(
                Event.check_name))).all()}
        events = sorted([{'name': x, 'count': y} for x, y in events.items()],
                        key=lambda x: (-x['count'], x['name']))
    else:
        events = events_query.filter(*filters_list).all_dict_out()
    return jsonify({'events': events})


@api.route('/events/<zone>/<client>/<check>')
def event(zone, client, check):
    extra = request.args.get('extra')
    filters = ((zone, Event.zone_name),
               (client, Event.client_name),
               (check, Event.check_name))
    filters_list = get_filters_list(filters)
    events = Event.query.filter(*filters_list)
    if extra == 'true':
        events = events.all_dict_extra_out_or_404()
    else:
        events = events.all_dict_out_or_404()
    return jsonify({'events': events})


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
    checks = checks_query.filter(*filters_list).all_dict_out()
    return jsonify({'checks': checks})


@api.route('/checks/<zone>/<check>')
def check(zone, check):
    extra = request.args.get('extra')
    filters = ((zone, Check.zone_name),
               (check, Check.name))
    filters_list = get_filters_list(filters)
    checks = Check.query.filter(*filters_list)
    if extra == 'true':
        checks = checks.all_dict_extra_out_or_404()
    else:
        checks = checks.all_dict_out_or_404()
    return jsonify({'checks': checks})


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
        dash_filters_list = Client.get_dashboard_filters_list(
            config, dashboard)
        clients_query = Client.query.filter(*dash_filters_list)
    else:
        clients_query = Client.query
    clients = clients_query.filter(*filters_list).all_dict_out()
    return jsonify({'clients': clients})


@api.route('/clients/<zone>/<client>')
def client(zone, client):
    filters = ((zone, Client.zone_name),
               (client, Client.name))
    filters_list = get_filters_list(filters)
    clients = Client.query.filter(*filters_list).all_dict_out_or_404()
    return jsonify({'clients': clients})


@api.route('/clients/<zone>/<client>/events')
def client_events(zone, client):
    filters = ((zone, Event.zone_name),
               (client, Event.client_name))
    filters_list = get_filters_list(filters)
    events = Event.query.filter(*filters_list).all_dict_out_or_404()
    return jsonify({'events': events})


@api.route('/clients/<zone>/<client>/events/<check>')
def client_events_check(zone, client, check):
    filters = ((zone, Event.zone_name),
               (client, Event.client_name),
               (check, Event.check_name))
    filters_list = get_filters_list(filters)
    events = Event.query.filter(*filters_list).all_dict_out_or_404()
    return jsonify({'events': events})


@api.route('/clients/<zone>/<client>/results')
def client_results(zone, client):
    filters = ((zone, Result.zone_name),
               (client, Result.client_name))
    filters_list = get_filters_list(filters)
    results = Result.query.filter(*filters_list).all_dict_out_or_404()
    return jsonify({'results': results})


@api.route('/clients/<zone>/<client>/results/<check>')
def client_results_check(zone, client, check):
    filters = ((zone, Result.zone_name),
               (client, Result.client_name),
               (check, Result.check_name))
    filters_list = get_filters_list(filters)
    results = Result.query.filter(*filters_list).all_dict_out_or_404()
    return jsonify({'results': results})


@api.route('/clients/<zone>/<client>/silences')
def client_silences(zone, client):
    filters = ((zone, Silence.zone_name),
               (client, Silence.client_name))
    filters_list = get_filters_list(filters)
    silences = Silence.query.filter(*filters_list).all_dict_out_or_404()
    return jsonify({'silences': silences})


@api.route('/silences')
def silences():
    zones = request.args.get('zone')
    clients = request.args.get('client')
    checks = request.args.get('check')
    filters = ((zones, Silence.zone_name),
               (clients, Silence.client_name),
               (checks, Silence.check_name))
    filters_list = get_filters_list(filters)
    silences = Silence.query.filter(*filters_list).all_dict_out()
    return jsonify({'silences': silences})
