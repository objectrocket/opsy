import aiohttp
import asyncio
from flask import json
from ..cache import *
from . import SensuBase


class SensuClient(SensuBase, Client):
    uri = 'clients'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.name = extra['name']
        extra['zone_name'] = zone_name
        self.extra = json.dumps(extra)


class SensuCheck(SensuBase, Check):
    uri = 'checks'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.name = extra['name']
        extra['zone_name'] = zone_name
        self.extra = json.dumps(extra)


class SensuResult(SensuBase, Result):
    uri = 'results'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.extra = extra
        self.client_name = extra['client']
        self.check_name = extra['check']['name']
        self.status = extra['check']['status']
        extra['zone_name'] = zone_name
        self.extra = json.dumps(extra)


class SensuEvent(SensuBase, Event):
    uri = 'events'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.client_name = extra['client']['name']
        self.check_name = extra['check']['name']
        self.check_occurrences = extra['check'].get('occurrences')
        self.event_occurrences = extra['occurrences']
        self.status = extra['check']['status']
        extra['zone_name'] = zone_name
        self.extra = json.dumps(extra)


class SensuStash(SensuBase, Stash):
    uri = 'stashes'

    def __init__(self, zone_name, extra):
        self.zone_name = zone_name
        self.path = extra['path']
        try:
            path_list = self.path.split('/')
            self.flavor = path_list[0]
            self.client_name = path_list[1]
            try:
                self.check_name = path_list[2]
            except IndexError:
                self.check_name = None
            self.source = extra['content']['source']
        except:
            self.flavor = None
            self.client_name = None
            self.check_name = None
            self.source = None
            self.created_at = None
            self.expire_at = None
        extra['zone_name'] = self.zone_name
        extra['check_name'] = self.check_name
        extra['client_name'] = self.client_name
        extra['flavor'] = self.flavor
        self.extra = json.dumps(extra)


class SensuZoneMetadata(SensuBase, ZoneMetadata):

    def __init__(self, zone_name, key, value):
        self.zone_name = zone_name
        self.key = key
        self.value = value


class SensuZone(SensuBase, Zone):

    def __repr__(self):
        return '<SensuZone %s>' % self.name
