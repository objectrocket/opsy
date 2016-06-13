from . import main
from flask import render_template, redirect, url_for, current_app


@main.context_processor
def inject_data():
    data = {
        'dashboards': current_app.config['dashboards'],
        'uchiwa_url': current_app.config['hourglass']['uchiwa_url'],
    }
    return data


@main.route('/')
def index():
    return redirect(url_for('main.events'))


@main.route('/events')
def events():
    return render_template('events.html', title='Events')


@main.route('/checks')
def checks():
    return render_template('checks.html', title='Checks')


@main.route('/clients')
def clients():
    return render_template('clients.html', title='Clients')


@main.route('/clients/<zone>/<client>')
def client(zone, client):
    return render_template('client_details.html', zone=zone,
                           client=client, title='Client Details')


@main.route('/about')
def about():
    return render_template('about.html', title='About')
