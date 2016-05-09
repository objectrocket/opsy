import requests

from . import api
from functools import wraps
from flask import json, current_app
from time import time


def with_config(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        config = current_app.config
        return func(config, *args, **kwargs)
    return func_wrapper


@api.route('/ping')
def ping():
    return json.dumps({'pong': time()})


@api.route('/events')
@api.route('/events/<datacenter>')
@with_config
def events(config, datacenter=None):
    sensu_nodes = config.get('sensu_nodes')
    hourglass_config = config.get('hourglass')
    events = []
    if datacenter:
        hosts = {datacenter: sensu_nodes.get(datacenter)}
    else:
        hosts = sensu_nodes
    for name, details in hosts.iteritems():
        url = 'http://%s:%s/events' % (details['host'], details['port'])
        localevents = requests.get(url).json()
        for event in localevents:
            age = int(time() - event['timestamp'])
            event.update({'datacenter': name})
        events += localevents
    for event in events:
        uchiwa_url = '%s/#/client/%s/%s?check=%s' % (
            hourglass_config['uchiwa_url'], event['datacenter'],
            event['client']['name'], event['check']['name'])
        event.update({
            'lastcheck': age,
            'href': uchiwa_url})
    return(json.dumps({'events': events, 'timestamp': time()}))


@api.route('/checks')
@api.route('/checks/<datacenter>')
@with_config
def checks(config, datacenter=None):
    sensu_nodes = config.get('sensu_nodes')
    checks = []
    if datacenter:
        hosts = {datacenter: sensu_nodes.get(datacenter)}
    else:
        hosts = sensu_nodes
    for name, details in hosts.iteritems():
        url = 'http://%s:%s/checks' % (details['host'], details['port'])
        localchecks = requests.get(url).json()
        for check in localchecks:
            check.update({'datacenter': name})
        checks += localchecks
    return(json.dumps({'checks': checks, 'timestamp': time()}))
