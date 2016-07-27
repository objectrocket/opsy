from hourglass.app import create_app
import uwsgi


config = uwsgi.opt.get('hourglass_config', './hourglass.ini')
app = create_app(config)
