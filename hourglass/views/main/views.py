import requests
from . import main
from flask import render_template, current_app, redirect, url_for, json
from time import time
from humanize import naturaltime


@main.route('/')
def index():
    return redirect(url_for('main.events'))

@main.route('/events')
def events(datacenter=None):
    return render_template('events.html', title='Events')

@main.route('/checks')
def checks(datacenter=None):
    return render_template('checks.html', title='Checks')

@main.route('/about')
def about():
    return render_template('about.html', title='About')
