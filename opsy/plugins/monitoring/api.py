from opsy.db import db
from opsy.utils import get_filters_list
from opsy.plugins.monitoring.backends.base import Client, Check, Result, \
    Event, Silence, Zone
from flask import Blueprint, current_app, jsonify, request


monitoring_api = Blueprint('monitoring_api', __name__)  # pylint: disable=invalid-name


@monitoring_api.route('/zones')
def zones():
    dashboard = request.args.get('dashboard')
    if dashboard:
        config = current_app.config
        dash_filters_list = Zone.get_dashboard_filters_list(config, dashboard)
        zone_list = Zone.query.filter(*dash_filters_list).all_dict_out_or_404()
    else:
        zone_list = Zone.query.filter().all_dict_out()
    return jsonify({'zones': zone_list})


@monitoring_api.route('/zones/<zone_name>')
def zone(zone_name):
    zoneobj = Zone.query.filter(Zone.name == zone_name).all_dict_out_or_404()
    return jsonify({'zone': zoneobj})


@monitoring_api.route('/events')
def events():
    dashboard = request.args.get('dashboard')
    count_checks = bool('count_checks' in request.args)
    hide_silenced = request.args.get('hide_silenced', '')
    reqzones = request.args.get('zone')
    reqchecks = request.args.get('check')
    reqclients = request.args.get('client')
    reqstatuses = request.args.get('status')
    filters = ((reqzones, Event.zone_name),
               (reqchecks, Event.check_name),
               (reqclients, Event.client_name),
               (reqstatuses, Event.status))
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
            Event.occurrences < Event.occurrences_threshold))
    if dashboard:
        config = current_app.config
        dash_filters_list = Event.get_dashboard_filters_list(config, dashboard)
        events_query = Event.query.filter(*dash_filters_list)
    else:
        events_query = Event.query
    if count_checks:
        event_list = {x: y for x, y in events_query.with_entities(
            Event.check_name, db.func.count(Event.check_name)).filter(
                *filters_list).group_by(
                    Event.check_name).order_by(db.desc(db.func.count(
                        Event.check_name))).all()}
        event_list = sorted([{'name': x, 'count': y} for x, y in event_list.items()],
                            key=lambda x: (-x['count'], x['name']))
    else:
        event_list = events_query.filter(*filters_list).all_dict_out()
    return jsonify({'events': event_list})


@monitoring_api.route('/events/<zone_name>/<client_name>/<check_name>')
def event(zone_name, client_name, check_name):
    extra = request.args.get('extra')
    filters = ((zone_name, Event.zone_name),
               (client_name, Event.client_name),
               (check_name, Event.check_name))
    filters_list = get_filters_list(filters)
    event_list = Event.query.filter(*filters_list)
    if extra:
        event_list = event_list.all_dict_extra_out_or_404()
    else:
        event_list = event_list.all_dict_out_or_404()
    return jsonify({'events': event_list})


@monitoring_api.route('/checks')
def checks():
    dashboard = request.args.get('dashboard')
    zone_list = request.args.get('zone')
    check_list = request.args.get('check')
    filters = ((zone_list, Check.zone_name),
               (check_list, Check.name))
    filters_list = get_filters_list(filters)
    if dashboard:
        config = current_app.config
        dash_filters_list = Check.get_dashboard_filters_list(config, dashboard)
        checks_query = Check.query.filter(*dash_filters_list)
    else:
        checks_query = Check.query
    check_list = checks_query.filter(*filters_list).all_dict_out()
    return jsonify({'checks': check_list})


@monitoring_api.route('/checks/<zone_name>/<check_name>')
def check(zone_name, check_name):
    extra = request.args.get('extra')
    filters = ((zone_name, Check.zone_name),
               (check_name, Check.name))
    filters_list = get_filters_list(filters)
    check_list = Check.query.filter(*filters_list)
    if extra == 'true':
        check_list = check_list.all_dict_extra_out_or_404()
    else:
        check_list = check_list.all_dict_out_or_404()
    return jsonify({'checks': check_list})


@monitoring_api.route('/clients')
def clients():
    dashboard = request.args.get('dashboard')
    zone_list = request.args.get('zone')
    client_list = request.args.get('client')
    filters = ((zone_list, Client.zone_name),
               (client_list, Client.name))
    filters_list = get_filters_list(filters)
    if dashboard:
        config = current_app.config
        dash_filters_list = Client.get_dashboard_filters_list(
            config, dashboard)
        clients_query = Client.query.filter(*dash_filters_list)
    else:
        clients_query = Client.query
    client_list = clients_query.filter(*filters_list).all_dict_out()
    return jsonify({'clients': client_list})


@monitoring_api.route('/clients/<zone_name>/<client_name>')
def client(zone_name, client_name):
    filters = ((zone_name, Client.zone_name),
               (client_name, Client.name))
    filters_list = get_filters_list(filters)
    client_list = Client.query.filter(*filters_list).all_dict_out_or_404()
    return jsonify({'clients': client_list})


@monitoring_api.route('/clients/<zone_name>/<client_name>/events')
def client_events(zone_name, client_name):
    filters = ((zone_name, Event.zone_name),
               (client_name, Event.client_name))
    filters_list = get_filters_list(filters)
    event_list = Event.query.filter(*filters_list).all_dict_out_or_404()
    return jsonify({'events': event_list})


@monitoring_api.route('/clients/<zone_name>/<client_name>/events/<check_name>')
def client_events_check(zone_name, client_name, check_name):
    filters = ((zone_name, Event.zone_name),
               (client_name, Event.client_name),
               (check_name, Event.check_name))
    filters_list = get_filters_list(filters)
    event_list = Event.query.filter(*filters_list).all_dict_out_or_404()
    return jsonify({'events': event_list})


@monitoring_api.route('/clients/<zone_name>/<client_name>/results')
def client_results(zone_name, client_name):
    filters = ((zone_name, Result.zone_name),
               (client_name, Result.client_name))
    filters_list = get_filters_list(filters)
    result_list = Result.query.filter(*filters_list).all_dict_out_or_404()
    return jsonify({'results': result_list})


@monitoring_api.route('/clients/<zone_name>/<client_name>/results/<check_name>')
def client_results_check(zone_name, client_name, check_name):
    filters = ((zone_name, Result.zone_name),
               (client_name, Result.client_name),
               (check_name, Result.check_name))
    filters_list = get_filters_list(filters)
    result_list = Result.query.filter(*filters_list).all_dict_out_or_404()
    return jsonify({'results': result_list})


@monitoring_api.route('/clients/<zone_name>/<client_name>/silences')
def client_silences(zone_name, client_name):
    filters = ((zone_name, Silence.zone_name),
               (client_name, Silence.client_name))
    filters_list = get_filters_list(filters)
    silence_list = Silence.query.filter(*filters_list).all_dict_out_or_404()
    return jsonify({'silences': silence_list})


@monitoring_api.route('/silences')
def silences():
    zone_list = request.args.get('zone')
    client_list = request.args.get('client')
    check_list = request.args.get('check')
    filters = ((zone_list, Silence.zone_name),
               (client_list, Silence.client_name),
               (check_list, Silence.check_name))
    filters_list = get_filters_list(filters)
    silence_list = Silence.query.filter(*filters_list).all_dict_out()
    return jsonify({'silences': silence_list})
