from flask import Blueprint, render_template, redirect, url_for, flash
from flask_allows import requires
from flask_login import current_user
from opsy.access import is_logged_in
from opsy.auth import login, logout
from opsy.schema import use_args_with, UserLoginSchema


core_main = Blueprint('core_main', __name__,  # pylint: disable=invalid-name
                      template_folder='templates',
                      static_url_path='/static',
                      static_folder='static')


@core_main.route('/')
def about():
    return render_template('about.html', title='About')


@core_main.route('/login', methods=['POST'])
@use_args_with(UserLoginSchema, locations=('form',))
def user_login(args):
    user = login(args['user_name'], args['password'],
                 remember=args['remember_me'])
    if not user:
        flash('Username or password incorrect.')
        return redirect(url_for('core_main.about'))
    return redirect(url_for('core_main.about'))


@core_main.route('/logout')
@requires(is_logged_in)
def user_logout():
    logout(current_user)
    return redirect(url_for('core_main.about'))
