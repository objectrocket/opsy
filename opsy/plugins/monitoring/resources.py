from flask import abort, jsonify
from flask_allows import requires
from flask_restful import Resource, reqparse
from opsy.access import HasPermission
from opsy.plugins.monitoring.backends.base import Client, Check, Result, \
    Event, Silence, Zone
from opsy.plugins.monitoring.dashboard import Dashboard
from opsy.plugins.monitoring.access import (
    dashboards_read, zones_read, events_read, checks_read, results_read,
    silences_read, clients_read)


class ZonesAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('dashboard', type=str)
        super().__init__()

    @requires(HasPermission(zones_read))
    def get(self):
        args = self.reqparse.parse_args()
        zones = Zone.query.wtfilter_by(
            prune_none_values=True, name=args['zone'],
            dashboard=args['dashboard']).all_dict_out()
        return jsonify({'zones': zones})


class ZoneAPI(Resource):

    @requires(HasPermission(zones_read))
    def get(self, zone_name):  # pylint: disable=no-self-use
        zones = Zone.query.wtfilter_by(name=zone_name).all_dict_out_or_404()
        return jsonify({'zones': zones})


class EventsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('count_checks', type=bool)
        self.reqparse.add_argument('truncate', type=bool)
        self.reqparse.add_argument('hide')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('client')
        self.reqparse.add_argument('check')
        self.reqparse.add_argument('status')
        super().__init__()

    @requires(HasPermission(events_read))
    def get(self):
        args = self.reqparse.parse_args()
        events_query = Event.query.wtfilter_by(
            prune_none_values=True,
            zone_name=args['zone'], client_name=args['client'],
            check_name=args['check'], status=args['status'],
            hide=args['hide'], dashboard=args['dashboard'])
        if args['count_checks']:
            events = events_query.count_checks()
        else:
            events = events_query.all_dict_out(truncate=args['truncate'])
        return jsonify({'events': events})


class ChecksAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('check')
        super().__init__()

    @requires(HasPermission(checks_read))
    def get(self):
        args = self.reqparse.parse_args()
        checks = Check.query.wtfilter_by(
            prune_none_values=True,
            zone_name=args['zone'], dashboard=args['dashboard'],
            name=args['check']).all_dict_out()
        return jsonify({'checks': checks})


class CheckAPI(Resource):

    @requires(HasPermission(checks_read))
    def get(self, zone_name, check_name):
        checks = Check.query.wtfilter_by(
            zone_name=zone_name,
            name=check_name).all_dict_out_or_404()
        return jsonify({'checks': checks})


class SilencesAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('client')
        self.reqparse.add_argument('check')
        self.reqparse.add_argument('subscription')
        super().__init__()

    @requires(HasPermission(silences_read))
    def get(self):
        args = self.reqparse.parse_args()
        silences = Silence.query.wtfilter_by(
            prune_none_values=True,
            zone_name=args['zone'], client_name=args['client'],
            check_name=args['check'], subscription=args['subscription'],
            dashboard=args['dashboard']).all_dict_out()
        return jsonify({'silences': silences})


class SilenceAPI(Resource):

    @requires(HasPermission(silences_read))
    def get(self, zone_name, silence_id):
        silences = Silence.query.wtfilter_by(
            zone_name=zone_name,
            id=silence_id).all_dict_out_or_404(all_attrs=True)
        return jsonify({'silences': silences})


class ClientsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('client')
        super().__init__()

    @requires(HasPermission(clients_read))
    def get(self):
        args = self.reqparse.parse_args()
        clients = Client.query.wtfilter_by(
            prune_none_values=True,
            zone_name=args['zone'], name=args['client'],
            dashboard=args['dashboard']).all_dict_out()
        return jsonify({'clients': clients})


class ClientAPI(Resource):

    @requires(HasPermission(clients_read))
    def get(self, zone_name, client_name):
        clients = Client.query.wtfilter_by(
            zone_name=zone_name,
            name=client_name).all_dict_out_or_404(all_attrs=True)
        return jsonify({'clients': clients})


class ClientEventsAPI(Resource):

    @requires(HasPermission(clients_read))
    def get(self, zone_name, client_name):
        event_list = Event.query.wtfilter_by(
            zone_name=zone_name,
            client_name=client_name).all_dict_out()
        return jsonify({'events': event_list})


class ClientEventAPI(Resource):

    @requires(HasPermission(clients_read))
    def get(self, zone_name, client_name, check_name):
        events = Event.query.wtfilter_by(
            zone_name=zone_name,
            client_name=client_name,
            check_name=check_name).all_dict_out_or_404(all_attrs=True)
        return jsonify({'events': events})


class ClientResultsAPI(Resource):

    @requires(HasPermission(clients_read))
    def get(self, zone_name, client_name):
        results = Result.query.wtfilter_by(
            zone_name=zone_name,
            client_name=client_name).all_dict_out()
        return jsonify({'results': results})


class ClientResultAPI(Resource):

    @requires(HasPermission(clients_read))
    def get(self, zone_name, client_name, check_name):
        results = Result.query.wtfilter_by(
            zone_name=zone_name,
            client_name=client_name,
            check_name=check_name).all_dict_out_or_404(all_attrs=True)
        return jsonify({'results': results})


class DashboardsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name')
        super().__init__()

    @requires(HasPermission(dashboards_read))
    def get(self):
        args = self.reqparse.parse_args()
        dashboard_list = Dashboard.query.wtfilter_by(
            prune_none_values=True, name=args['name']).all_dict_out()
        return jsonify({'dashboards': dashboard_list})


class DashboardAPI(Resource):

    @requires(HasPermission(dashboards_read))
    def get(self, dashboard_name):  # pylint: disable=no-self-use
        dashboard_list = Dashboard.query.wtfilter_by(name=dashboard_name).dict_out
        return jsonify({'dashboard': dashboard_list})
