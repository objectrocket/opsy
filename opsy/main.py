from flask import Blueprint, render_template, request, redirect, url_for, abort
from flask_login import login_required, login_user, logout_user
from opsy.auth.models import User
# from opsy.db import db


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
            user = User.get_by_name(request.form['username'])
        except ValueError:
            return abort(401)
        password = request.form['password']
        if user.verify_password(password):
            login_user(user)
            return redirect(url_for('core_main.about'))
        else:
            return abort(401)
    return redirect(url_for('about'))


@core_main.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('core_main.about'))
