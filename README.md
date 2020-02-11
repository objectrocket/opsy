# Opsy

It's Opsy! A simple multi-user/role operations inventory system with aspirations.

# Installing - Helm

Helm charts are available for Opsy, the repo for Opsy can be setup like so:

    $ helm repo add objectrocket-opsy https://objectrocket.github.io/opsy/helm
    "objectrocket-opsy" has been added to your repositories
    $ helm search opsy
    NAME                    CHART VERSION           APP VERSION     DESCRIPTION                                                 
    objectrocket-opsy/opsy  0.0.1+0.3.1.0rc2        0.3.1.0rc2      It's Opsy! A simple multi-user/role operations inventory ...

The chart can accept nearly all the configuration options that can be provided to the Docker image, a complete list ias available in `helm/opsy/values.yaml`, here are the more important ones:

| Variable               | Default | Description                                                              |
| ---------------------- | ------- | ------------------------------------------------------------------------ |
| admin_password         | `none`  | Password for the admin user. Required.                                   |
| database_uri           | `none`  | The connection string for the DB. Required.                              |
| secret_key             | `none`  | The secret key. Required.                                                |

Example usage:

    $ helm install objectrocket-opsy/opsy --set opsy.admin_password=password --set opsy.app.secret_key='this is a secret' --set opsy.app.database_uri='postgresql://opsy:password@myneatdb.example.com/opsy' --set ingress.hosts[0].host="example.com" --set ingress.hosts[0].paths[0]="/opsy" --set ingress.enabled=true --version 0.0.1+0.3.1.0rc3

# Installing - Docker image

The included Dockerfile can be used to create a docker image for Opsy. The entrypoint script accepts environment variables to configure Opsy. A full mapping of the variables can be found in `scripts/entrypoint.sh`, here are the more important ones:

| Variable               | Default | Description                                                              |
| ---------------------- | ------- | ------------------------------------------------------------------------ |
| OPSY_CREATE_ADMIN_USER | `true`  | Controls if the admin user should be created.                            |
| OPSY_ADMIN_PASSWORD    | `none`  | Password for the admin user. Required if OPSY_CREATE_ADMIN_USER is true. |
| OPSY_MIGRATE_DB        | `true`  | Controls if the DB schema should be migrated.                            |
| OPSY_RUN               | `true`  | Controls if the Opsy app should be started.                              |
| OPSY_DATABASE_URI      | `none`  | The connection string for the DB. Required.                              |
| OPSY_SECRET_KEY        | `none`  | The secret key. Required.                                                |

The Docker image can be built by running `make`.

Example usage:

    $ docker run --name opsy-test -d -p 5000:5000 -e OPSY_DATABASE_URI='postgresql://opsy:password@myneatdb.example.com/opsy' -e OPSY_SECRET_KEY='this is a secret' -e OPSY_ADMIN_PASSWORD='password' objectrocket/opsy:0.3.1.0rc3

# Installing - Pip

First setup a virtual environment for Opsy:

    $ mkvirtualenv -p /usr/bin/python3.6 opsy

Then install it:

    $ pip install opsy

Copy the example config and make any needed modifications to it:

    $ cp opsy.toml.example opsy.toml
    $ vim opsy.toml

Then apply the DB migrations:

    $ opsyctl db upgrade -d ${VIRTUAL_ENV}/opsy_data/migrations

You can now create your admin user and set its password, create a role, then add the user to the role:

    $ opsyctl create-admin-user

Each route is protected by a permission for that route. You can get a full list of the permissions by running `opsyctl permission-list`. Permissions are granted to roles and users gain access to permissions by being in roles. The admin user and role created with the last command are automatically granted full permissions.

We are now ready to start opsy for the first time:

    $ opsyctl run

By default it listens on `http://127.0.0.1:5000/`. You can access the auto generated swagger docs by navigating to `http://127.0.0.1:5000/docs/`.

# Developing
It's recommended to use a virtual environment for development.

    $ mkvirtualenv -p /usr/bin/python3.6 opsy

Clone down the opsy repo:

    $ git clone git@github.com:objectrocket/opsy.git

Install opsy for development (ensure you are in your previously created virtualenv):

    $ pip install --editable .

Create opsy.toml by copying the example config:

    $ cp opsy.toml.example opsy.toml

Initialize the DB, the example config uses sqlite by default for development:

    $ opsyctl db upgrade

# Dealing with schema changes

If you are introducing a change that requires a schema change you must create a schema revision. This can be done like so:

    $ opsyctl db migrate

This will autogenerate a new revision file under `migrations/versions/`. Please review the resulting file and make any changes necessary to account for changes that Alembic doesn't do a good job of detecting (things like table renames). Please review the following documentation for more information:
https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect

If you are upgrading Opsy and need to migrate to a newer version of the schema you can run the following:

    $ opsyctl db upgrade
