# Opsy
It's Opsy! A simple multi-user/role operations inventory system with aspirations. Test.

# Developing
It's recommended to use a virtual environment for development.

    $ mkvirtualenv -p /usr/bin/python3.6 opsy

Clone down the opsy repo:

    $ git clone git@github.com:testeddoughnut/opsy.git

Install opsy for development (ensure you are in your previously created virtualenv):

    $ pip install --editable .

Create opsy.ini by copying the example config:

    $ cp opsy.ini.example opsy.ini

Initialize the DB, the example config uses sqlite by default for development:

    $ opsy init-db

You can now create your first user and role, then add the user to the role:

    $ opsy user create admin
    $ opsy role create admins
    $ opsy role add-user admins admin

Each route is protected by a permission for that route. You can get a full list of the permissions by running `opsy permission-list`. Permissions are granted to roles and users gain access to permissions by being in roles. For now let's add all the permissions to our new role, something like this should do that:

    $ for x in $(opsy permission-list | grep api | awk '{print $6}' | sort | uniq); do opsy role add-permission admins $x; done

We are now ready to start opsy for the first time:

    $ opsy run

By default it listens on `http://127.0.0.1:5000/`. You can access the auto generated swagger docs by navigating to `http://127.0.0.1:5000/docs/`.
