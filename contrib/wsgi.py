from hourglass import create_app
from uwsgi_tasks import timer
import uwsgi


config = uwsgi.opt.get('hourglass_config', './hourglass.ini')
app = create_app(config)


@timer(seconds=0, iterations=1)
def run_poller_at_start(signum):
    app.scheduler.run_tasks()


@timer(seconds=app.scheduler.interval)
def run_poller(signum):
    app.scheduler.run_tasks()
