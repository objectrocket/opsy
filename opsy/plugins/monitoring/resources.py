from flask import jsonify
from flask_restful import Resource, reqparse
from opsy.utils import get_filters_list
from opsy.plugins.monitoring.backends.base import Client, Check, Result, \
    Event, Silence, Zone
from opsy.plugins.monitoring.dashboard import Dashboard


class ZonesAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('dashboard', type=str)
        super().__init__()

    def get(self):
        args = self.reqparse.parse_args()
        zones = Zone.filter(zones=args['zone'],
                            dashboard=args['dashboard']).all_dict_out()
        return jsonify({'zones': zones})


class ZoneAPI(Resource):

    def get(self, zone_name):  # pylint: disable=no-self-use
        zones = Zone.filter(zones=zone_name).all_dict_out_or_404()
        return jsonify({'zones': zones})


class EventsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('extra', type=bool, default=False)
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('count_checks', type=bool)
        self.reqparse.add_argument('hide_silenced')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('client')
        self.reqparse.add_argument('check')
        self.reqparse.add_argument('status')
        super().__init__()

    def get(self):
        args = self.reqparse.parse_args()

        events_query = Event.filter(
            zones=args['zone'], clients=args['client'],
            checks=args['check'], statuses=args['status'],
            hide_silenced=args['hide_silenced'], dashboard=args['dashboard'])
        if args['count_checks']:
            events = events_query.count_checks()
        else:
            events = events_query.all_dict_out(extra=args['extra'])
        return jsonify({'events': events})


class ChecksAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('extra', type=bool, default=False)
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('check')
        super().__init__()

    def get(self):
        args = self.reqparse.parse_args()
        checks = Check.filter(
            zones=args['zone'],
            checks=args['check']).all_dict_out(extra=args['extra'])
        return jsonify({'checks': checks})


class CheckAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('extra', type=bool, default=False)
        super().__init__()

    def get(self, zone_name, check_name):
        args = self.reqparse.parse_args()
        checks = Check.filter(
            zones=args['zone'],
            checks=args['check']).all_dict_out_or_404(extra=args['extra'])
        return jsonify({'checks': checks})


class SilencesAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('extra', type=bool, default=False)
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('client')
        self.reqparse.add_argument('check')
        self.reqparse.add_argument('type', choices=['check', 'client'])
        super().__init__()

    def get(self):
        args = self.reqparse.parse_args()
        silences = Silence.filter(
            zones=args['zone'], clients=args['client'], checks=args['check'],
            types=args['type']).all_dict_out(extra=args['extra'])
        return jsonify({'silences': silences})


class ClientsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('extra', type=bool, default=False)
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('client')
        super().__init__()

    def get(self):
        args = self.reqparse.parse_args()
        clients = Client.filter(
            zones=args['zone'], clients=args['client'],
            dashboard=args['dashboard']).all_dict_out(extra=args['extra'])
        return jsonify({'clients': clients})


class ClientAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('extra', type=bool, default=False)
        super().__init__()

    def get(self, zone_name, client_name):
        args = self.reqparse.parse_args()
        clients = Client.filter(
            zones=zone_name,
            clients=client_name).all_dict_out_or_404(extra=args['extra'])
        return jsonify({'clients': clients})


class ClientEventsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('extra', type=bool, default=False)
        super().__init__()

    def get(self, zone_name, client_name):
        args = self.reqparse.parse_args()
        event_list = Event.filter(
            zones=zone_name,
            clients=client_name).all_dict_out(extra=args['extra'])
        return jsonify({'events': event_list})


class ClientEventAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('extra', type=bool, default=False)
        super().__init__()

    def get(self, zone_name, client_name, check_name):
        args = self.reqparse.parse_args()
        events = Event.filter(
            zones=zone_name,
            clients=client_name,
            checks=check_name).all_dict_out_or_404(extra=args['extra'])
        return jsonify({'events': events})


class ClientResultsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('extra', type=bool, default=False)
        super().__init__()

    def get(self, zone_name, client_name):
        args = self.reqparse.parse_args()
        results = Result.filter(
            zones=zone_name,
            clients=client_name).all_dict_out(extra=args['extra'])
        return jsonify({'results': results})


class ClientResultAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('extra', type=bool, default=False)
        super().__init__()

    def get(self, zone_name, client_name, check_name):
        args = self.reqparse.parse_args()
        results = Result.filter(
            zones=zone_name,
            clients=client_name,
            checks=check_name).all_dict_out_or_404(extra=args['extra'])
        return jsonify({'results': results})


class ClientSilencesAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('extra', type=bool, default=False)
        self.reqparse.add_argument('type', choices=['check', 'client'])
        super().__init__()

    def get(self, zone_name, client_name):
        args = self.reqparse.parse_args()
        silences = Silence.filter(
            zones=zone_name,
            clients=client_name,
            types=args['type']).all_dict_out(extra=args['extra'])
        return jsonify({'silences': silences})


class ClientSilenceAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('extra', type=bool, default=False)
        super().__init__()

    def get(self, zone_name, client_name, check_name):
        args = self.reqparse.parse_args()
        silences = Silence.filter(
            zones=zone_name,
            clients=client_name,
            checks=check_name).all_dict_out_or_404(extra=args['extra'])
        return jsonify({'silences': silences})


class DashboardsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name')
        super().__init__()

    def get(self):
        args = self.reqparse.parse_args()
        filters = ((args['name'], Dashboard.name),)
        filters_list = get_filters_list(filters)
        dashboard_list = Dashboard.get(
            output_query=True, filters_list=filters_list).all_dict_out()
        return jsonify({'dashboards': dashboard_list})


class DashboardAPI(Resource):

    def get(self, dashboard_name):  # pylint: disable=no-self-use
        dashboard_list = Dashboard.get_by_name(dashboard_name).dict_out
        return jsonify({'dashboard': dashboard_list})
