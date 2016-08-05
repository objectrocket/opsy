# Opsy
A multi user/group web dashboard for Sensu

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

# Building a deb package

Install the packaging dependencies:
`apt-get install dh-virtualenv debhelper`

Enter the root of the repository and build the package:
`dpkg-buildpackage -us -uc`

# F.A.Q.

- Why Python3.4... Python 2.7 is where it's at!
  - The poller relies on asyncio which is only present in Python 3.4+
