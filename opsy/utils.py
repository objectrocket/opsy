from datetime import date
import uuid
from flask.json import JSONEncoder
from flask._compat import text_type
from itsdangerous import json as _json
from dateutil.tz import tzutc
from stevedore import driver


class OpsyJSONEncoder(JSONEncoder):

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


def load_plugins(app):
    opsy_config = app.config.get('opsy')
    plugins = opsy_config.get('enabled_plugins')
    if plugins:
        for plugin in plugins.split(','):
            plugin_manager = driver.DriverManager(
                namespace='opsy.plugin',
                name=plugin,
                invoke_args=(app,),
                invoke_on_load=True)
            yield plugin_manager.driver
