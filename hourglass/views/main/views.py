import requests
import json
from . import main
from flask import render_template, current_app, redirect, url_for


@main.route('/')
def index():
    return redirect(url_for('main.events'))

@main.route('/events')
@main.route('/events/<datacenter>')
def events(datacenter=None):
    app = current_app._get_current_object()
    HGCONFIG = app.config.get('hourglass_config')
    if datacenter:
        host = [i['host'] for i in HGCONFIG['sensu'] if i['name'] == datacenter][0]
        events = json.loads(requests.get('http://'+host+':4567/events').content)
    else:
        hosts = [i['host'] for i in HGCONFIG['sensu']]
        events = []
        for host in hosts:
            events += json.loads(requests.get('http://'+host+':4567/events').content)
    return render_template('events.html', title='Events', events=events)


@main.route('/checks')
@main.route('/checks/<datacenter>')
def checks(datacenter=None):
    app = current_app._get_current_object()
    HGCONFIG = app.config.get('hourglass_config')
    if datacenter:
        host = [i['host'] for i in HGCONFIG['sensu'] if i['name'] == datacenter][0]
        checks = json.loads(requests.get('http://'+host+':4567/checks').content)
    else:
        hosts = [i['host'] for i in HGCONFIG['sensu']]
        checks = []
        for host in hosts:
            checks += json.loads(requests.get('http://'+host+':4567/checks').content)
    return render_template('checks.html', title='Checks', checks=checks)

@main.route('/about')
def about():
    return render_template('about.html', title='About')
