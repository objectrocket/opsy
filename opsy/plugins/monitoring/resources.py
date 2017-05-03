from flask import abort, jsonify
from flask_restful import Resource, reqparse
from opsy.plugins.monitoring.backends.base import Client, Check, Result, \
    Event, Silence, Zone
from opsy.plugins.monitoring.dashboard import Dashboard
from opsy.plugins.monitoring.access import permissions


class ZonesAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('dashboard', type=str)
        super().__init__()

    def get(self):
        if not permissions.get('zones_read').can():
            abort(403)
        args = self.reqparse.parse_args()
        zones = Zone.query.wtfilter_by(
            prune_none_values=True, name=args['zone'],
            dashboard=args['dashboard']).all_dict_out()
        return jsonify({'zones': zones})


class ZoneAPI(Resource):

    def get(self, zone_name):  # pylint: disable=no-self-use
        if not permissions.get('zones_read').can():
            abort(403)
        zones = Zone.query.wtfilter_by(name=zone_name).all_dict_out_or_404()
        return jsonify({'zones': zones})


class EventsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('count_checks', type=bool)
        self.reqparse.add_argument('hide_silenced')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('client')
        self.reqparse.add_argument('check')
        self.reqparse.add_argument('status')
        super().__init__()

    def get(self):
        if not permissions.get('events_read').can():
            abort(403)
        args = self.reqparse.parse_args()
        events_query = Event.query.wtfilter_by(
            prune_none_values=True,
            zone_name=args['zone'], client_name=args['client'],
            check_name=args['check'], status=args['status'],
            hide_silenced=args['hide_silenced'], dashboard=args['dashboard'])
        if args['count_checks']:
            events = events_query.count_checks()
        else:
            events = events_query.all_dict_out()
        return jsonify({'events': events})


class ChecksAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('check')
        super().__init__()

    def get(self):
        if not permissions.get('checks_read').can():
            abort(403)
        args = self.reqparse.parse_args()
        checks = Check.query.wtfilter_by(
            prune_none_values=True,
            zone_name=args['zone'], dashboard=args['dashboard'],
            name=args['check']).all_dict_out()
        return jsonify({'checks': checks})


class CheckAPI(Resource):

    def get(self, zone_name, check_name):
        if not permissions.get('checks_read').can():
            abort(403)
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

    def get(self):
        if not permissions.get('silences_read').can():
            abort(403)
        args = self.reqparse.parse_args()
        silences = Silence.query.wtfilter_by(
            prune_none_values=True,
            zone_name=args['zone'], client_name=args['client'],
            check_name=args['check'], subscription=args['subscription'],
            dashboard=args['dashboard']).all_dict_out()
        return jsonify({'silences': silences})


class SilenceAPI(Resource):

    def get(self, zone_name, silence_id):
        if not permissions.get('silences_read').can():
            abort(403)
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

    def get(self):
        if not permissions.get('clients_read').can():
            abort(403)
        args = self.reqparse.parse_args()
        clients = Client.query.wtfilter_by(
            prune_none_values=True,
            zone_name=args['zone'], name=args['client'],
            dashboard=args['dashboard']).all_dict_out()
        return jsonify({'clients': clients})


class ClientAPI(Resource):

    def get(self, zone_name, client_name):
        if not permissions.get('clients_read').can():
            abort(403)
        clients = Client.query.wtfilter_by(
            zone_name=zone_name,
            name=client_name).all_dict_out_or_404(all_attrs=True)
        return jsonify({'clients': clients})


class ClientEventsAPI(Resource):

    def get(self, zone_name, client_name):
        if not permissions.get('clients_read').can():
            abort(403)
        event_list = Event.query.wtfilter_by(
            zone_name=zone_name,
            client_name=client_name).all_dict_out()
        return jsonify({'events': event_list})


class ClientEventAPI(Resource):

    def get(self, zone_name, client_name, check_name):
        if not permissions.get('clients_read').can():
            abort(403)
        events = Event.query.wtfilter_by(
            zone_name=zone_name,
            client_name=client_name,
            check_name=check_name).all_dict_out_or_404(all_attrs=True)
        return jsonify({'events': events})


class ClientResultsAPI(Resource):

    def get(self, zone_name, client_name):
        if not permissions.get('clients_read').can():
            abort(403)
        results = Result.query.wtfilter_by(
            zone_name=zone_name,
            client_name=client_name).all_dict_out()
        return jsonify({'results': results})


class ClientResultAPI(Resource):

    def get(self, zone_name, client_name, check_name):
        if not permissions.get('clients_read').can():
            abort(403)
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

    def get(self):
        if not permissions.get('dashboards_read').can():
            abort(403)
        args = self.reqparse.parse_args()
        dashboard_list = Dashboard.query.wtfilter_by(
            prune_none_values=True, name=args['name']).all_dict_out()
        return jsonify({'dashboards': dashboard_list})


class DashboardAPI(Resource):

    def get(self, dashboard_name):  # pylint: disable=no-self-use
        if not permissions.get('dashboards_read').can():
            abort(403)
        dashboard_list = Dashboard.query.wtfilter_by(name=dashboard_name).dict_out
        return jsonify({'dashboard': dashboard_list})
