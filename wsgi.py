from hourglass import create_app
from uwsgidecorators import timer


app = create_app('./hourglass.ini')
app.scheduler.create_cache_db()


@timer(app.scheduler.interval)
def run_poller(signum):
    app.scheduler.run_tasks()
