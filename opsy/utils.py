import copy
import uuid
import sys
from collections import Mapping
from datetime import date
from operator import attrgetter
from flask import json, current_app
from flask._compat import text_type
from itsdangerous import json as _json
from dateutil.tz import tzutc
from stevedore import driver


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


def load_plugins(app):
    if not app.config.opsy['enabled_plugins']:
        return
    for plugin in app.config.opsy['enabled_plugins']:
        plugin_manager = driver.DriverManager(
            namespace='opsy.plugin',
            name=plugin,
            invoke_args=(app,),
            invoke_on_load=True)
        yield plugin_manager.driver


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


# pylint: disable=too-many-branches
def merge_dict(dest, upd, recursive_update=True, merge_lists=False):
    """
    Recursive version of the default dict.update.

    Merges upd recursively into dest
    If recursive_update=False, will use the classic dict.update, or fall back
    on a manual merge (helpful for non-dict types like FunctionWrapper)
    If merge_lists=True, will aggregate list object types instead of replace.
    The list in ``upd`` is added to the list in ``dest``, so the resulting list
    is ``dest[key] + upd[key]``. This behavior is only activated when
    recursive_update=True. By default merge_lists=False.
    .. versionchanged: 2016.11.6
        When merging lists, duplicate values are removed. Values already
        present in the ``dest`` list are not added from the ``upd`` list.
    """
    if (not isinstance(dest, Mapping)) \
            or (not isinstance(upd, Mapping)):
        raise TypeError(
            'Cannot update using non-dict types in dictupdate.update()')
    updkeys = list(upd.keys())
    if not set(list(dest.keys())) & set(updkeys):
        recursive_update = False
    if recursive_update:
        for key in updkeys:
            val = upd[key]
            try:
                dest_subkey = dest.get(key, None)
            except AttributeError:
                dest_subkey = None
            if isinstance(dest_subkey, Mapping) \
                    and isinstance(val, Mapping):
                ret = merge_dict(dest_subkey, val, merge_lists=merge_lists)
                dest[key] = ret
            elif isinstance(dest_subkey, list) \
                    and isinstance(val, list):
                if merge_lists:
                    merged = copy.deepcopy(dest_subkey)
                    merged.extend([x for x in val if x not in merged])
                    dest[key] = merged
                else:
                    dest[key] = upd[key]
            else:
                dest[key] = upd[key]
        return dest
    try:
        for k in upd:
            dest[k] = upd[k]
    except AttributeError:
        # this mapping is not a dict
        for k in upd:
            dest[k] = upd[k]
    return dest


def get_protected_routes(ignored_methods=None):
    if ignored_methods is None:
        ignored_methods = ["HEAD", "OPTIONS"]
    permissions = []
    rules = list(current_app.url_map.iter_rules())
    if not rules:
        return permissions

    rules = sorted(rules, key=attrgetter('endpoint'))

    rule_methods = [", ".join(sorted(rule.methods - set(ignored_methods)))
                    for rule in rules]

    for rule, method in zip(rules, rule_methods):
        view_func = current_app.view_functions[rule.endpoint]
        if getattr(view_func, '__rbac__', False):
            permissions.append(
                {
                    'endpoint': rule.rule,
                    'method': method,
                    'permission_needed': view_func.__rbac__[
                        'permission_needed']
                })
    return permissions
