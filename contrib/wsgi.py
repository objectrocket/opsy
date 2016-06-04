from hourglass import create_app
from uwsgidecorators import timer
import uwsgi


config = uwsgi.opt.get('hourglass_config', './hourglass.ini')
app = create_app(config)
app.scheduler.create_cache_db()


@timer(app.scheduler.interval)
def run_poller(signum):
    app.scheduler.run_tasks()
