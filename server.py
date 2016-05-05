import requests

from flask import json
from flask import Flask, render_template
app = Flask(__name__)

HGCONFIG = {}

def get_config(path='./hourglass.json'):
    global HGCONFIG
    if len(HGCONFIG) > 0:
        return HGCONFIG
    with open('./hourglass.json') as conffile:
        HGCONFIG = json.load(conffile)
    return HGCONFIG

@app.route('/')
def index():
    return render_template('main.html', title='FOO')

@app.route('/events')
@app.route('/events/<datacenter>')
def events(datacenter=None):
    if datacenter:
        host = [i['host'] for i in HGCONFIG['sensu'] if i['name'] == datacenter][0]
        events = json.loads(requests.get('http://'+host+':4567/events').content)
    else:
        hosts = [i['host'] for i in HGCONFIG['sensu']]
        events = []
        for host in hosts:
            events += json.loads(requests.get('http://'+host+':4567/events').content)
    return render_template('events.html', title='Events', events=events)

@app.route('/checks')
@app.route('/checks/<datacenter>')
def checks(datacenter=None):
    checks = json.loads(requests.get('http://watcher.cryptkcoding.com:4567/checks').content)
    return render_template('checks.html', title='Checks', checks=checks)

if __name__ == "__main__":
    get_config()
    app.run(debug=True, host='0.0.0.0')
