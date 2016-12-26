import os.path
from collections import namedtuple
from functools import partial
from opsy.extensions import iniconfig
from opsy.exceptions import NoConfigFile, NoConfigSection, MissingConfigOption

MappedFlaskConfigOption = namedtuple(  # pylint: disable=invalid-name
    'ConfigOption', ['flask_mapping', 'name', 'type', 'required', 'default'])
ConfigOption = partial(  # pylint: disable=invalid-name
    MappedFlaskConfigOption, None)

DEFAULT_FLASK_CONFIG = {
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
}

CONFIG_OPTIONS = [
    MappedFlaskConfigOption('SECRET_KEY', 'secret_key', str, True, None),
    MappedFlaskConfigOption('SQLALCHEMY_DATABASE_URI', 'database_uri', str,
                            True, None),
    ConfigOption('enabled_plugins', list, False, None),
    ConfigOption('scheduler_grace_time', int, False, 10),
    ConfigOption('log_file', str, False, None),
    ConfigOption('session_token_ttl', int, False, 86400)
]


def validate_config(app, plugin=None):
    if plugin:
        section_name = plugin.name
        config_options = plugin.config_options
    else:
        section_name = 'opsy'
        config_options = CONFIG_OPTIONS
    if not hasattr(app.config, section_name):
        if any([x.required for x in config_options]):
            raise NoConfigSection('Config section "%s" does not exist in '
                                  'config file "%s".' % (section_name,
                                                         app.config_file))
        setattr(app.config, section_name, {})
    section_config = getattr(app.config, section_name)
    for option in config_options:
        if not section_config.get(option.name):
            if option.required:
                raise MissingConfigOption('Required config option "%s" missing'
                                          ' from config section "%s" in config'
                                          ' file "%s".' % (
                                              option.name, section_name,
                                              app.config_file))
            section_config[option.name] = option.default
        if (section_config[option.name] is not None and
                not isinstance(section_config[option.name], option.type)):
            raise TypeError('Expected "%s" type for config option "%s" from '
                            'config section "%s" in config file "%s".' % (
                                option.type.__name__, option.name,
                                section_name, app.config_file))
        if option.flask_mapping:
            app.config[option.flask_mapping] = section_config[option.name]
            section_config.pop(option.name)


def load_config(app, config_file):
    for key, value in DEFAULT_FLASK_CONFIG.items():
        app.config[key] = value
    iniconfig.init_app(app)
    if not os.path.exists(config_file):
        raise NoConfigFile('Config file "%s" does not exist.' % config_file)
    app.config_file = config_file
    app.config.from_inifile(app.config_file, objectify=True)
    validate_config(app)
