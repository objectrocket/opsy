from time import time
from . import api
from hourglass.models.api import get_events, get_checks
from flask import current_app, json


@api.route('/ping')
def ping():
    return json.dumps({'pong': time()})


@api.route('/events')
@api.route('/events/<datacenter>')
def events(datacenter=None):
    sensuevents = get_events(current_app.config, datacenter)
    return json.dumps({'events': sensuevents, 'timestamp': time()})


@api.route('/checks')
@api.route('/checks/<datacenter>')
def checks(datacenter=None):
    sensuchecks = get_checks(current_app.config, datacenter)
    return json.dumps({'checks': sensuchecks, 'timestamp': time()})
