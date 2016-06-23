from hourglass import create_app, create_devapp
from uwsgi_tasks import timer
import uwsgi


config = uwsgi.opt.get('hourglass_config', './hourglass.ini')
dev_mode = uwsgi.opt.get('dev_mode', 'False')

if dev_mode == b'True':
    app = create_devapp(config)
else:
    app = create_app(config)


@timer(seconds=0, iterations=1)
def run_poller_at_start(signum):
    app.scheduler.create_cache_db()


@timer(seconds=app.scheduler.interval)
def run_poller(signum):
    app.scheduler.run_tasks()
