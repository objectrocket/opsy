from datetime import date
import importlib
import uuid
from flask.json import JSONEncoder
from flask._compat import text_type
from itsdangerous import json as _json
from dateutil.tz import tzutc


class HourglassJSONEncoder(JSONEncoder):

    def default(self, o):  # pylint: disable=method-hidden
        if isinstance(o, date):
            # TODO (testeddoughnut): proper timezone support
            o = o.replace(tzinfo=tzutc())
            return o.isoformat()
        if isinstance(o, uuid.UUID):
            return str(o)
        if hasattr(o, '__html__'):
            return text_type(o.__html__())
        return _json.JSONEncoder.default(self, o)


def load_zones(config):
    zones = []
    for name, zone_config in config['zones'].items():
        backend = zone_config.get('backend')
        package = backend.split(':')[0]
        class_name = backend.split(':')[1]
        zone_module = importlib.import_module(package)
        zone_class = getattr(zone_module, class_name)
        zones.append(zone_class(name, **zone_config))
    return zones


def get_filters_list(filters):
    filters_list = []
    for items, db_object in filters:
        if items:
            include, exclude = parse_include_excludes(items)
            if include:
                filters_list.append(db_object.in_(include))
            if exclude:
                filters_list.append(~db_object.in_(exclude))
    return filters_list


def parse_include_excludes(items):
    if items:
        item_list = items.split(',')
        # Wrap in a set to remove duplicates
        include = list(set([x for x in item_list if not x.startswith('!')]))
        exclude = list(set([x[1:] for x in item_list if x.startswith('!')]))
    else:
        include, exclude = [], []
    return include, exclude
