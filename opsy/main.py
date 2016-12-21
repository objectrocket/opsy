from flask import Blueprint, render_template
# from opsy.auth.models import User
# from opsy.db import db


core_main = Blueprint('core_main', __name__,  # pylint: disable=invalid-name
                      template_folder='templates',
                      static_url_path='/static',
                      static_folder='static')


@core_main.route('/')
def about():
    return render_template('about.html', title='About')


# @core_main.route('/register', methods=['GET','POST'])
# def register():
#     if request.method == 'GET':
#         return render_template('register.html')
#     user = User(request.form['username'] , request.form['password'],request.form['email'])
#     db.session.add(user)
#     db.session.commit()
#     flash('User successfully registered')
#     return redirect(url_for('login'))


# @core_main.route('/login',methods=['GET','POST'])
# def login():
#     if request.method == 'GET':
#         return render_template('login.html')
#     return redirect(url_for('index'))
