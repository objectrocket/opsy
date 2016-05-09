from . import api
from time import time
from hourglass.models.api import get_events, get_checks
from flask import current_app, json


@api.route('/ping')
def ping():
    return json.dumps({'pong': time()})


@api.route('/events')
@api.route('/events/<datacenter>')
def events(datacenter=None):
    events = get_events(current_app.config, datacenter)
    return(json.dumps({'events': events, 'timestamp': time()}))


@api.route('/checks')
@api.route('/checks/<datacenter>')
def checks(datacenter=None):
    checks = get_checks(current_app.config, datacenter)
    return(json.dumps({'checks': checks, 'timestamp': time()}))
