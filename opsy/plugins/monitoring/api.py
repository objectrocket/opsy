from flask import Blueprint
from flask_restful import Api
from opsy.plugins.monitoring.resources import ZonesAPI, ZoneAPI, EventsAPI, \
    ChecksAPI, CheckAPI, SilencesAPI, ClientsAPI, ClientAPI, ClientEventsAPI, \
    ClientEventAPI, ClientResultsAPI, ClientResultAPI, ClientSilencesAPI, \
    ClientSilenceAPI, DashboardsAPI, DashboardAPI


monitoring_api = Blueprint('monitoring_api', __name__)  # pylint: disable=invalid-name
api = Api(monitoring_api)  # pylint: disable=invalid-name

api.add_resource(
    ZonesAPI, '/zones',
    endpoint='zones')
api.add_resource(
    ZoneAPI, '/zones/<zone_name>',
    endpoint='zone')
api.add_resource(
    EventsAPI, '/events',
    endpoint='events')
api.add_resource(
    ChecksAPI, '/checks',
    endpoint='checks')
api.add_resource(
    CheckAPI, '/checks/<zone_name>/<check_name>',
    endpoint='check')
api.add_resource(
    SilencesAPI, '/silences',
    endpoint='silences')
api.add_resource(
    ClientsAPI, '/clients',
    endpoint='clients')
api.add_resource(
    ClientAPI, '/clients/<zone_name>/<client_name>',
    endpoint='client')
api.add_resource(
    ClientEventsAPI, '/clients/<zone_name>/<client_name>/events',
    endpoint='client_events')
api.add_resource(
    ClientEventAPI, '/clients/<zone_name>/<client_name>/events/<check_name>',
    endpoint='client_event')
api.add_resource(
    ClientResultsAPI, '/clients/<zone_name>/<client_name>/results',
    endpoint='client_results')
api.add_resource(
    ClientResultAPI, '/clients/<zone_name>/<client_name>/results/<check_name>',
    endpoint='client_result')
api.add_resource(
    ClientSilencesAPI, '/clients/<zone_name>/<client_name>/silences',
    endpoint='client_silences')
api.add_resource(
    ClientSilenceAPI, '/clients/<zone_name>/<client_name>/silences/<check_name>',
    endpoint='client_silence')
api.add_resource(
    DashboardsAPI, '/dashboards',
    endpoint='dashboards')
api.add_resource(
    DashboardAPI, '/dashboards/<dashboard_name>',
    endpoint='dashboard')
