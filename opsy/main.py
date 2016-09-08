from flask import Blueprint, render_template


core_main = Blueprint('core_main', __name__,  # pylint: disable=invalid-name
                      template_folder='templates',
                      static_url_path='/static',
                      static_folder='static')


@core_main.route('/')
def index():
    return render_template('about.html', title='About')
