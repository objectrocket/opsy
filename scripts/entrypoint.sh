#!/bin/bash

set -e

if [ -z "${OPSY_DATABASE_URI}" ] || [ -z "${OPSY_SECRET_KEY}" ]; then
    echo 'OPSY_DATABASE_URI and OPSY_SECRET_KEY must be set, exiting.'
    exit 1
fi

cat > ${OPSY_CONFIG} <<__EOF__
[app]
database_uri = '${OPSY_DATABASE_URI}'
secret_key = '${OPSY_SECRET_KEY}'
uri_prefix = '${OPSY_URI_PREFIX:-/}'

[server]
host = '0.0.0.0'
port = 5000
threads = ${OPSY_THREADS:-10}

[logging]
log_level = '${OPSY_LOG_LEVEL:-INFO}'

[auth]
base_permissions = ${OPSY_BASE_PERMISSIONS:-[]}
logged_in_permissions = ${OPSY_LOGGED_IN_PERMISSIONS:-[]}
session_token_ttl = ${OPSY_SESSION_TOKEN_TTL:-86400}
ldap_enabled = ${OPSY_LDAP_ENABLED:-false}
ldap_host = '${OPSY_LDAP_HOST:-}'
ldap_port = ${OPSY_LDAP_PORT:-389}
ldap_use_ssl = ${OPSY_LDAP_USE_SSL:-false}
ldap_bind_user_dn = '${OPSY_LDAP_BIND_USER_DN:-}'
ldap_bind_user_password = '${OPSY_LDAP_BIND_USER_PASSWORD:-}'
ldap_base_dn = '${OPSY_LDAP_BASE_DN:-}'
ldap_user_dn = '${OPSY_LDAP_USER_DN:-}'
ldap_user_object_filter = '${OPSY_LDAP_USER_OBJECT_FILTER:-}'
ldap_user_login_attr = '${OPSY_LDAP_USER_LOGIN_ATTR:-}'
ldap_user_rdn_attr = '${OPSY_LDAP_USER_RDN_ATTR:-}'
ldap_user_full_name_attr = '${OPSY_LDAP_USER_FULL_NAME_ATTR:-}'
ldap_user_email_attr = '${OPSY_LDAP_USER_EMAIL_ATTR:-}'
ldap_user_search_scope = '${OPSY_LDAP_USER_SEARCH_SCOPE:-LEVEL}'
ldap_group_dn = '${OPSY_LDAP_GROUP_DN:-}'
ldap_group_object_filter = '${OPSY_LDAP_GROUP_OBJECT_FILTER:-}'
ldap_group_members_attr = '${OPSY_LDAP_GROUP_MEMBERS_ATTR:-}'
ldap_group_name_attr = '${OPSY_LDAP_GROUP_NAME_ATTR:-}'
ldap_group_search_scope = '${OPSY_LDAP_GROUP_SEARCH_SCOPE:-LEVEL}'
__EOF__

# Migrate the DB schema
if [ "${OPSY_MIGRATE_DB:-true}" = true ]; then
    /opt/opsy/bin/opsyctl db upgrade -d /opt/opsy/opsy_data/migrations
fi

# Create the admin user
if [ "${OPSY_CREATE_ADMIN_USER:-true}" = true ]; then
    if [ -z "${OPSY_ADMIN_PASSWORD}" ]; then
        echo 'OPSY_ADMIN_PASSWORD must be set to create admin user, exiting.'
        exit 1
    fi
    /opt/opsy/bin/opsyctl create-admin-user
fi

# Remove passwords
unset OPSY_DATABASE_URI OPSY_SECRET_KEY OPSY_LDAP_BIND_USER_PASSWORD OPSY_ADMIN_PASSWORD

# Now run the app
if [ "${OPSY_RUN:-true}" = true ]; then
    /opt/opsy/bin/opsyctl run
fi
