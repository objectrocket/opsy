from flask import jsonify
from flask_allows import requires, And
from flask_restful import Resource, reqparse
from opsy.access import HasPermission
from opsy.plugins.monitoring.backends.base import Client, Check, Result, \
    Event, Silence, Zone
from opsy.plugins.monitoring.dashboard import Dashboard
from opsy.plugins.monitoring.access import (
    DASHBOARDS_READ, ZONES_READ, EVENTS_READ, CHECKS_READ, RESULTS_READ,
    SILENCES_READ, CLIENTS_READ)
from opsy.plugins.monitoring.schema import (
    ClientSchema, CheckSchema, ResultSchema, EventSchema, SilenceSchema,
    ZoneSchema, DashboardSchema)


class ZonesAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('dashboard', type=str)
        super().__init__()

    @requires(HasPermission(ZONES_READ))
    def get(self):
        args = self.reqparse.parse_args()
        zones = Zone.query.wtfilter_by(
            prune_none_values=True, name=args['zone'],
            dashboard=args['dashboard'])
        return ZoneSchema(many=True).jsonify(zones)


class ZoneAPI(Resource):

    @requires(HasPermission(ZONES_READ))
    def get(self, zone_name):  # pylint: disable=no-self-use
        zone = Zone.query.wtfilter_by(name=zone_name).first()
        return ZoneSchema().jsonify(zone)


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

    @requires(HasPermission(EVENTS_READ))
    def get(self):
        args = self.reqparse.parse_args()
        events_query = Event.query.wtfilter_by(
            prune_none_values=True,
            zone_name=args['zone'], client_name=args['client'],
            check_name=args['check'], status=args['status'],
            hide=args['hide'], dashboard=args['dashboard'])
        if args['count_checks']:
            events = events_query.count_checks()
            return jsonify(events_query.count_checks())
        events = events_query
        return EventSchema(many=True).jsonify(events)


class ChecksAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('check')
        super().__init__()

    @requires(HasPermission(CHECKS_READ))
    def get(self):
        args = self.reqparse.parse_args()
        checks = Check.query.wtfilter_by(
            prune_none_values=True,
            zone_name=args['zone'], dashboard=args['dashboard'],
            name=args['check'])
        return CheckSchema(many=True).jsonify(checks)


class CheckAPI(Resource):

    @requires(HasPermission(CHECKS_READ))
    def get(self, zone_name, check_name):
        check = Check.query.wtfilter_by(
            zone_name=zone_name,
            name=check_name).first()
        return CheckSchema().jsonify(check)


class SilencesAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('client')
        self.reqparse.add_argument('check')
        self.reqparse.add_argument('subscription')
        super().__init__()

    @requires(HasPermission(SILENCES_READ))
    def get(self):
        args = self.reqparse.parse_args()
        silences = Silence.query.wtfilter_by(
            prune_none_values=True,
            zone_name=args['zone'], client_name=args['client'],
            check_name=args['check'], subscription=args['subscription'],
            dashboard=args['dashboard'])
        return SilenceSchema(many=True).jsonify(silences)


class SilenceAPI(Resource):

    @requires(HasPermission(SILENCES_READ))
    def get(self, zone_name, silence_id):
        silence = Silence.query.wtfilter_by(
            zone_name=zone_name,
            id=silence_id).first()
        return SilenceSchema().jsonify(silence)


class ClientsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('dashboard')
        self.reqparse.add_argument('zone')
        self.reqparse.add_argument('client')
        super().__init__()

    @requires(HasPermission(CLIENTS_READ))
    def get(self):
        args = self.reqparse.parse_args()
        clients = Client.query.wtfilter_by(
            prune_none_values=True,
            zone_name=args['zone'], name=args['client'],
            dashboard=args['dashboard'])
        return ClientSchema(many=True).jsonify(clients)


class ClientAPI(Resource):

    @requires(HasPermission(CLIENTS_READ))
    def get(self, zone_name, client_name):
        client = Client.query.wtfilter_by(
            zone_name=zone_name,
            name=client_name).first()
        return ClientSchema().jsonify(client)


class ClientEventsAPI(Resource):

    @requires(And(HasPermission(CLIENTS_READ), HasPermission(EVENTS_READ)))
    def get(self, zone_name, client_name):
        events = Event.query.wtfilter_by(
            zone_name=zone_name,
            client_name=client_name)
        return EventSchema(many=True).jsonify(events)


class ClientEventAPI(Resource):

    @requires(And(HasPermission(CLIENTS_READ), HasPermission(EVENTS_READ)))
    def get(self, zone_name, client_name, check_name):
        event = Event.query.wtfilter_by(
            zone_name=zone_name,
            client_name=client_name,
            check_name=check_name).first()
        return EventSchema().jsonify(event)


class ClientResultsAPI(Resource):

    @requires(And(HasPermission(CLIENTS_READ), HasPermission(RESULTS_READ)))
    def get(self, zone_name, client_name):
        results = Result.query.wtfilter_by(
            zone_name=zone_name,
            client_name=client_name)
        return ResultSchema(many=True).jsonify(results)


class ClientResultAPI(Resource):

    @requires(And(HasPermission(CLIENTS_READ), HasPermission(RESULTS_READ)))
    def get(self, zone_name, client_name, check_name):
        result = Result.query.wtfilter_by(
            zone_name=zone_name,
            client_name=client_name,
            check_name=check_name).first()
        return ResultSchema().jsonify(result)


class DashboardsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name')
        super().__init__()

    @requires(HasPermission(DASHBOARDS_READ))
    def get(self):
        args = self.reqparse.parse_args()
        dashboards = Dashboard.query.wtfilter_by(
            prune_none_values=True, name=args['name'])
        return DashboardSchema(many=True).jsonify(dashboards)


class DashboardAPI(Resource):

    @requires(HasPermission(DASHBOARDS_READ))
    def get(self, dashboard_name):  # pylint: disable=no-self-use
        dashboard = Dashboard.query.wtfilter_by(name=dashboard_name).first()
        return DashboardSchema().jsonify(dashboard)
