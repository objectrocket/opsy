# Opsy
The ultimate operations dashboard. Provides a framework for operations tools.

# Developing
Create a virtualenvironment with virtualenvwrapper
`mkvirtualenv -p /path/to/python3.4 opsy`

Clone down the opsy source code
`git clone git@github.com:cryptk/opsy.git`

Install opsy for development (ensure you are in your previously created virtualenv)
`~/opsy $ pip install --editable .`

Run the app via uWSGI
`~/opsy $ uwsgi -M --wsgi-file contrib/uwsgi/wsgi.py --callable app --http-socket 0.0.0.0:5000 --processes 4 --mule=contrib/uwsgi/scheduler.py`

This should start the app server on http://127.0.0.1:5000/

# Using the CLI utility
Opsy comes with a CLI utility to interact with its database models or to perform some tasks. This can be invoked by running `opsy`. To see a full list of commands run `opsy --help`. This can also be used on subcommands, like `opsy monitoring --help`.

The CLI utility is also used for adding zones and dashboards for the monitoring plugin. Example:

    $ opsy monitoring zone create DEV sensu --host localhost --port 4567 --timeout 5 --interval 5 --enabled 1
    +----------------+------------------------------------------+
    | Property       | Value                                    |
    +----------------+------------------------------------------+
    | created_at     | 2016-12-12 18:25:35                      |
    | updated_at     | 2016-12-12 18:25:35                      |
    | id             | 6e8c630e-d747-4151-bf59-baf0708184f1     |
    | name           | DEV                                      |
    | backend        | sensu                                    |
    | last_poll_time | None                                     |
    | enabled        | True                                     |
    | status         | new                                      |
    | status_message | This zone is new and has not polled yet. |
    | host           | localhost                                |
    | path           | None                                     |
    | protocol       | http                                     |
    | port           | 4567                                     |
    | timeout        | 5                                        |
    | interval       | 5                                        |
    | username       | None                                     |
    | password       | None                                     |
    | verify_ssl     | True                                     |
    +----------------+------------------------------------------+
    $ opsy monitoring dashboard create DevTeam --description 'Board for the dev team' --enabled 1 --zone_filters 'DEV'
    +-------------+--------------------------------------+
    | Property    | Value                                |
    +-------------+--------------------------------------+
    | created_at  | 2016-12-12 18:25:42                  |
    | updated_at  | 2016-12-12 18:25:42                  |
    | id          | ba7ffd07-352b-4f84-9625-76b09b9b06ad |
    | name        | DevTeam                              |
    | description | Board for the dev team               |
    | enabled     | True                                 |
    +-------------+--------------------------------------+

# Building a deb package

Install the packaging dependencies:
`apt-get install dh-virtualenv debhelper`

Enter the root of the repository and build the package:
`dpkg-buildpackage -us -uc`

# F.A.Q.

- Why Python3.4... Python 2.7 is where it's at!
  - The poller relies on asyncio which is only present in Python 3.4+
