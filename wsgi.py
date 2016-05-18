from hourglass import create_app
from hourglass.models.poller import Poller
from uwsgidecorators import timer

app = create_app('./hourglass.ini')
poller = Poller(app)
poller.main()
poll_interval = app.config['hourglass'].get('poll_interval', 10)


@timer(poll_interval)
def run_poller(signum):
    poller.main()
