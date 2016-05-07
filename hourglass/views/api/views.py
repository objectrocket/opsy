import requests

from . import api
from flask import json, current_app
from time import time


@api.route('/ping')
def ping():
    return json.dumps({'pong': time()})

@api.route('/events')
@api.route('/events/<datacenter>')
def events(datacenter=None):
    app = current_app._get_current_object()
    HGCONFIG = app.config.get('hourglass_config')
    if datacenter:
        host = [{'host': i['host'], 'port': i['port']} for i in HGCONFIG['sensu'] if i['name'] == datacenter][0]
        events = json.loads(requests.get('http://'+host['host']+':'+str(host['port'])+'/events').content)
        for event in events:
            age = int(time() - event['timestamp'])
            event.update({"datacenter": datacenter})
    else:
        hosts = HGCONFIG['sensu']
        events = []
        for host in hosts:
            localevents = json.loads(requests.get('http://'+host['host']+':'+str(host['port'])+'/events').content)
            for event in localevents:
                age = int(time() - event['timestamp'])
                event.update({'datacenter': host['name']})
            events += localevents
    for event in events:
        event.update({
            'lastcheck': age,
            'href': HGCONFIG['hourglass']['uchiwa_url']+'/#/client/'+event['datacenter']+'/'+event['client']['name']+'?check='+event['check']['name']
            })
    return(json.dumps({'events': events, 'timestamp': time()}))


@api.route('/checks')
@api.route('/checks/<datacenter>')
def checks(datacenter=None):
    app = current_app._get_current_object()
    HGCONFIG = app.config.get('hourglass_config')
    if datacenter:
        host = [{'host': i['host'], 'port': i['port']} for i in HGCONFIG['sensu'] if i['name'] == datacenter][0]
        checks = json.loads(requests.get('http://'+host['host']+':'+str(host['port'])+'/checks').content)
        for check in checks:
            check.update({"datacenter": datacenter})
    else:
        hosts = HGCONFIG['sensu']
        checks = []
        for host in hosts:
            localchecks = json.loads(requests.get('http://'+host['host']+':'+str(host['port'])+'/checks').content)
            for check in localchecks:
                check.update({'datacenter': host['name']})
            checks += localchecks
    return(json.dumps({'checks': checks, 'timestamp': time()}))
