from datetime import datetime
from time import time
from flask import json
from opsy.plugins.monitoring.backends.base import Client, Check, Result, \
    Event, Silence, Zone, HttpZoneMixin


class SensuBase(object):
    __mapper_args__ = {
        'polymorphic_identity': 'sensu'
    }


class SensuClient(SensuBase, Client):
    uri = 'clients'

    def __init__(self, zone, extra):
        self.zone_id = zone.id
        self.zone_name = zone.name
        self.name = extra['name']
        try:
            self.updated_at = datetime.utcfromtimestamp(
                int(extra.get('timestamp')))
        except TypeError:
            self.updated_at = None
        self.version = extra.get('version')
        self.address = extra.get('address')
        self.extra = json.dumps(extra)


class SensuCheck(SensuBase, Check):
    uri = 'checks'

    def __init__(self, zone, extra):
        self.zone_id = zone.id
        self.zone_name = zone.name
        self.name = extra['name']
        self.occurrences_threshold = extra.get('occurrences')
        self.interval = extra.get('interval')
        self.command = extra.get('command')
        self.extra = json.dumps(extra)


class SensuResult(SensuBase, Result):
    uri = 'results'

    def __init__(self, zone, extra):
        self.zone_id = zone.id
        self.zone_name = zone.name
        self.client_name = extra['client']
        self.check_name = extra['check']['name']
        status_map = ['ok', 'warning', 'critical']
        try:
            self.status = status_map[extra['check'].get('status')]
        except IndexError:
            self.status = 'unknown'
        self.occurrences_threshold = extra['check'].get('occurrences')
        self.command = extra['check'].get('command')
        self.output = extra['check'].get('output')
        self.interval = extra['check'].get('interval')
        self.extra = json.dumps(extra)


class SensuEvent(SensuBase, Event):
    uri = 'events'

    def __init__(self, zone, extra):
        self.zone_id = zone.id
        self.zone_name = zone.name
        self.client_name = extra['client'].get('name')
        self.check_name = extra['check'].get('name')
        try:
            self.updated_at = datetime.utcfromtimestamp(
                int(extra.get('timestamp')))
        except TypeError:
            self.updated_at = None
        self.occurrences_threshold = extra['check'].get('occurrences')
        self.occurrences = extra['occurrences']
        status_map = ['ok', 'warning', 'critical']
        try:
            self.status = status_map[extra['check'].get('status')]
        except IndexError:
            self.status = 'unknown'
        self.command = extra['check'].get('command')
        self.output = extra['check'].get('output')
        self.interval = extra['check'].get('interval')
        self.extra = json.dumps(extra)


class SensuSilence(SensuBase, Silence):
    uri = 'stashes'

    def __init__(self, zone, extra):
        self.zone_id = zone.id
        self.zone_name = zone.name
        path_list = extra['path'].split('/')
        self.client_name = path_list[1]
        try:
            self.check_name = path_list[2]
        except IndexError:
            self.check_name = None
        if self.check_name:
            self.silence_type = 'check'
        else:
            self.silence_type = 'client'
        self.comment = json.dumps(extra['content'])
        if extra['content'].get('timestamp'):
            self.created_at = datetime.utcfromtimestamp(
                int(extra['content']['timestamp']))
        if extra['expire'] == -1:
            self.expire_at = None
        else:
            self.expire_at = datetime.utcfromtimestamp(
                int(time() + int(extra['expire'])))
        self.extra = json.dumps(extra)

    @classmethod
    def filter_api_response(cls, response):
        return [x for x in response if x['path'].startswith('silence/')]


class SensuZone(SensuBase, HttpZoneMixin, Zone):  # pylint: disable=too-many-ancestors

    models = [SensuCheck, SensuClient, SensuEvent, SensuSilence, SensuResult]

    def __init__(self, name, enabled=0, host=None, path=None, protocol='http',
                 port=4567, timeout=30, interval=30, username=None,
                 password=None, verify_ssl=True, **kwargs):
        super().__init__(name, enabled=enabled, host=host, path=path,
                         protocol=protocol, port=port, timeout=timeout,
                         interval=interval, username=username,
                         password=password, verify_ssl=verify_ssl, **kwargs)
