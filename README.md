# hourglass
A multi user/group web dashboard for Sensu

# Developing
Create a virtualenvironment with virtualenvwrapper
`mkvirtualenv hourglass`

Clone down the hourglass source code
`git clone git@github.com:cryptk/hourglass.git`

Install hourglass for development (ensure you are in your previously created virtualenv)
`~/hourglass $ pip install --editable .`

Run the development server
`~/hourglass $ hourglass runserver`

This should start the development server on http://127.0.0.1:5000/
