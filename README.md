# hourglass
A multi user/group web dashboard for Sensu

# Developing
Create a virtualenvironment with virtualenvwrapper
`mkvirtualenv -p /path/to/python3.4 hourglass`

Clone down the hourglass source code
`git clone git@github.com:cryptk/hourglass.git`

Install hourglass for development (ensure you are in your previously created virtualenv)
`~/hourglass $ pip install --editable .`

Run the app via uWSGI
`~/hourglass $ uwsgi -M --wsgi-file wsgi.py --callable app --http-socket 127.0.0.1:5000 --processes 2`

This should start the app server on http://127.0.0.1:5000/

# F.A.Q.

- Why Python3.4... Python 2.7 is where it's at!
  - The poller relies on asyncio which is only present in Python 3.4+
