from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user
from flask_principal import identity_changed, Identity, AnonymousIdentity
from opsy.auth.models import User


core_main = Blueprint('core_main', __name__,  # pylint: disable=invalid-name
                      template_folder='templates',
                      static_url_path='/static',
                      static_folder='static')


@core_main.route('/')
def about():
    return render_template('about.html', title='About')


@core_main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        try:
            user = User.get_or_fail(name=request.form['username']).first()
            if not user.verify_password(request.form['password']):
                flash('Username or password incorrect')
                return redirect(url_for('core_main.login'))
            user.get_session_token(current_app)  # ensure that a session token exists
            login_user(user, remember=True)
            identity_changed.send(
                current_app._get_current_object(),  # pylint: disable=W0212
                identity=Identity(user.id))
            return redirect(url_for('core_main.about'))
        except ValueError:
            flash('Username or password incorrect')
            return redirect(url_for('core_main.login'))


@core_main.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    identity_changed.send(
        current_app._get_current_object(),  # pylint: disable=W0212
        identity=AnonymousIdentity())
    return redirect(url_for('core_main.about'))
