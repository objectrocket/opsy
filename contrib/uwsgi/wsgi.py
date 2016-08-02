from opsy.app import create_app
import uwsgi


config = uwsgi.opt.get('opsy_config', './opsy.ini')
app = create_app(config)
