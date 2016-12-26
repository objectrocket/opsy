from flask import Blueprint, render_template, redirect, url_for, current_app


monitoring_main = Blueprint('monitoring_main', __name__,  # pylint: disable=invalid-name
                            template_folder='templates',
                            static_url_path='/static',
                            static_folder='static')


@monitoring_main.context_processor
def inject_data():
    data = {
        'uchiwa_url': current_app.config.monitoring['uchiwa_url']
    }
    return data


@monitoring_main.route('/')
def index():
    return redirect(url_for('monitoring_main.events'))


@monitoring_main.route('/events')
def events():
    return render_template('events.html', title='Events')


@monitoring_main.route('/checks')
def checks():
    return render_template('checks.html', title='Checks')


@monitoring_main.route('/clients')
def clients():
    return render_template('clients.html', title='Clients')


@monitoring_main.route('/clients/<zone>/<client_name>')
def client(zone, client_name):
    return render_template('client_details.html', zone=zone,
                           client=client_name, title='Client Details')


@monitoring_main.route('/clients/<zone>/<client_name>/events/<check>')
def client_event(zone, client_name, check):
    return render_template('client_event_details.html', zone=zone,
                           client=client_name, check=check, title='Event Details')
