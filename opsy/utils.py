from datetime import date
import uuid
import os.path
import sys
from flask import json
from flask._compat import text_type
from flask_iniconfig import INIConfig
from itsdangerous import json as _json
from prettytable import PrettyTable
from dateutil.tz import tzutc
from stevedore import driver
from opsy.exceptions import NoConfigFile, NoConfigSection


class OpsyJSONEncoder(json.JSONEncoder):

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
    opsy_config = get_config_section_or_fail(app, 'opsy')
    plugins = opsy_config.get('enabled_plugins')
    if plugins:
        for plugin in plugins.split(','):
            plugin_manager = driver.DriverManager(
                namespace='opsy.plugin',
                name=plugin,
                invoke_args=(app,),
                invoke_on_load=True)
            yield plugin_manager.driver


def get_config_section_or_fail(app, config_section):
    if not app.config.get(config_section):
        raise NoConfigSection('Config section "%s" does not exist' %
                              config_section)
    return app.config.get(config_section)


def load_config(app, config_file):
    if not os.path.exists(config_file):
        raise NoConfigFile('Config file "%s" does not exist' % config_file)
    app.config_file = config_file
    INIConfig(app)
    app.config.from_inifile(config_file)
    app.opsy_config = get_config_section_or_fail(app, 'opsy')


def print_property_table(properties, ignore_attrs=None):
    table = PrettyTable(['Property', 'Value'])
    table.align['Property'] = 'l'
    table.align['Value'] = 'l'
    for key, value in sorted(properties):
        if ignore_attrs and key in ignore_attrs:
            continue
        table.add_row([key, value])
    print(table)


def gwrap(some_string):
    """Returns green text."""
    return "\033[92m%s\033[0m" % some_string


def rwrap(some_string):
    """Returns red text."""
    return "\033[91m%s\033[0m" % some_string


def print_error(error, title=None, exit_script=True):
    if not title:
        title = "Something broke"
    print("[%s] %s" % (rwrap(title), error), file=sys.stderr)
    if exit_script:
        sys.exit(1)


def print_notice(msg, title=None):
    if not title:
        title = "Notice"
    print("[%s] %s" % (gwrap(title), msg))
