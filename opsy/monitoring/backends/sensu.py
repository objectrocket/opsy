from datetime import datetime
from flask import current_app
from marshmallow import EXCLUDE, pre_load
from werkzeug.urls import url_join
from opsy.flask_extensions import ma
from opsy.monitoring.backends.base import HttpPollerBackend


class SensuBackend(HttpPollerBackend):

    def __init__(self, monitoring_service, host='localhost', protocol='http',
                 port=4567, path='', interval=60, timeout=30, username=None,
                 password=None, verify_ssl=False):
        self.monitoring_service = monitoring_service
        self.protocol = protocol
        self.host = host
        self.port = port
        self.path = path
        self.interval = interval
        self.timeout = timeout
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl

    @property
    def urls(self):
        """This should return a list of generated URLs to be polled."""
        return [url_join(self.base_url, 'events')]

    def decode(self, data):
        """This performs the data decoding. Returns list of raw events."""
        events = []
        for event in SensuEventSchema(many=True).load(data[0]):
            if not event.pop('silenced', False):
                events.append(event)
        current_app.logger.debug(f'Got from sensu: {events}')
        return events


class SensuEventSchema(ma.Schema):

    class Meta:
        fields = ('host_name', 'check_name', 'status', 'command', 'output',
                  'silenced', 'occurrences', 'updated_at')
        unknown = EXCLUDE

    silenced = ma.Boolean()
    occurrences = ma.Number()
    updated_at = ma.Method(data_key='timestamp',
                           deserialize='convert_timestamp')
    host_name = ma.String()
    check_name = ma.String()
    status = ma.Method(deserialize='convert_status')
    command = ma.String(allow_none=True)
    output = ma.String(allow_none=True)

    def convert_status(self, value):
        statuses = ['ok', 'warning', 'critical']
        try:
            return statuses[value]
        except IndexError:
            return 'unknown'

    def convert_timestamp(self, value):
        try:
            return datetime.utcfromtimestamp(int(value))
        except TypeError:
            return None

    @pre_load
    def flatten(self, data):
        data['host_name'] = data['client'].get('name')
        data['check_name'] = data['check'].get('name')
        data['status'] = data['check'].get('status')
        data['command'] = data['check'].get('command')
        data['output'] = data['check'].get('output')
        return data
