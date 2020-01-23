import os.path
import toml
from marshmallow import (Schema, fields, validate, validates_schema,
                         ValidationError)
from opsy.exceptions import NoConfigFile


class ConfigAppSchema(Schema):
    database_uri = fields.Str(required=True)
    secret_key = fields.Str(required=True)
    uri_prefix = fields.Str(missing='/')


class ConfigAuthSchema(Schema):
    base_permissions = fields.List(fields.Str(), missing=[])
    logged_in_permissions = fields.List(fields.Str(), missing=[])
    session_token_ttl = fields.Integer(missing=86400)
    ldap_enabled = fields.Boolean(missing=False)
    ldap_host = fields.Str(missing=None)
    ldap_port = fields.Integer(missing=389)
    ldap_use_ssl = fields.Boolean(missing=False)
    ldap_bind_user_dn = fields.Str(missing=None)
    ldap_bind_user_password = fields.Str(missing=None)
    ldap_base_dn = fields.Str(missing='')
    ldap_user_dn = fields.Str(missing='')
    ldap_user_object_filter = fields.Str(missing='(objectclass=person)')
    ldap_user_login_attr = fields.Str(missing='uid')
    ldap_user_rdn_attr = fields.Str(missing='uid')
    ldap_user_full_name_attr = fields.Str(missing='displayName')
    ldap_user_email_attr = fields.Str(missing='mail')
    ldap_user_search_scope = fields.Str(
        validate=validate.OneOf(['LEVEL', 'SUBTREE']), missing='LEVEL')
    ldap_group_dn = fields.Str(missing='')
    ldap_group_object_filter = fields.Str(missing='(objectclass=groupOfNames)')
    ldap_group_members_attr = fields.Str(missing='Member')
    ldap_group_name_attr = fields.Str(missing='cn')
    ldap_group_search_scope = fields.Str(
        validate=validate.OneOf(['LEVEL', 'SUBTREE']), missing='LEVEL')

    @validates_schema
    def validate_ldap(self, data, **kwargs):
        if data.get('ldap_enabled') and not data.get('ldap_host'):
            raise ValidationError(
                'Auth option "ldap_host" is required when "ldap_enabled" is '
                'set to true.')


class ConfigLoggingSchema(Schema):
    log_file = fields.Str(missing=None)
    access_log_file = fields.Str(missing=None)
    log_level = fields.Str(
        validate=validate.OneOf(
            ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']),
        missing='INFO')


class ConfigServerSchema(Schema):
    host = fields.Str(missing='localhost')
    port = fields.Integer(missing=5000)
    threads = fields.Integer(missing=10)
    ssl_enabled = fields.Boolean(missing=False)
    certificate = fields.Str(missing=None)
    private_key = fields.Str(missing=None)
    ca_certificate = fields.Str(missing=None)

    @validates_schema
    def validate_ssl(self, data, **kwargs):
        if data.get('ssl_enabled'):
            certificate = data.get('certificate')
            private_key = data.get('private_key')
            if not all([certificate, private_key]):
                raise ValidationError(
                    'Server options "certificate" and "private_key" are '
                    'required when "ssl_enabled" is set to true.')


class ConfigSchema(Schema):
    app = fields.Nested(ConfigAppSchema(), required=True)
    auth = fields.Nested(
        ConfigAuthSchema(), missing=ConfigAuthSchema().load({}))
    logging = fields.Nested(
        ConfigLoggingSchema(), missing=ConfigLoggingSchema().load({}))
    server = fields.Nested(
        ConfigServerSchema(), missing=ConfigServerSchema().load({}))


def load_config(config_file):
    if not os.path.exists(config_file):
        raise NoConfigFile(f'File "{config_file}" does not exist.')
    with open(config_file, 'r') as file_handler:
        config = ConfigSchema().load(toml.load(file_handler))
    return config


def configure_app(app, config):
    app.config.update({
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JSON_SORT_KEYS': False,
        'SECRET_KEY': config['app']['secret_key'],
        'SQLALCHEMY_DATABASE_URI': config['app']['database_uri'],
        'LDAP_HOST': config['auth']['ldap_host'],
        'LDAP_PORT': config['auth']['ldap_port'],
        'LDAP_USE_SSL': config['auth']['ldap_use_ssl'],
        'LDAP_BIND_USER_DN': config['auth']['ldap_bind_user_dn'],
        'LDAP_BIND_USER_PASSWORD': config['auth']['ldap_bind_user_password'],
        'LDAP_BASE_DN': config['auth']['ldap_base_dn'],
        'LDAP_USER_DN': config['auth']['ldap_user_dn'],
        'LDAP_USER_OBJECT_FILTER': config['auth']['ldap_user_object_filter'],
        'LDAP_USER_LOGIN_ATTR': config['auth']['ldap_user_login_attr'],
        'LDAP_USER_RDN_ATTR': config['auth']['ldap_user_rdn_attr'],
        'LDAP_USER_SEARCH_SCOPE': config['auth']['ldap_user_search_scope'],
        'LDAP_GROUP_DN': config['auth']['ldap_group_dn'],
        'LDAP_GROUP_OBJECT_FILTER': config['auth']['ldap_group_object_filter'],
        'LDAP_GROUP_MEMBERS_ATTR': config['auth']['ldap_group_members_attr'],
        'LDAP_GROUP_SEARCH_SCOPE': config['auth']['ldap_group_search_scope']
    })
    setattr(app.config, 'opsy', config)
