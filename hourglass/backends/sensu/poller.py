from hourglass.backends.sensu.cache import *
from hourglass.backends.poller import Poller
import requests


class SensuPoller(Poller):

    def __init__(self, name, config):
        super().__init__(name, config)
        self.models = [SensuCheck, SensuClient, SensuEvent, SensuStash,
                       SensuResult]

    def query_api(self, app, uri):
        url = "http://%s:%s/%s" % (self.host, self.port, uri)
        app.logger.debug('Making request to %s' % url)
        try:
                response = requests.get(url, timeout=self.timeout)
                app.logger.debug('Response %s from %s' % (
                    response.status_code, url))
                return response.json()
        except requests.exceptions.Timeout:
            app.logger.debug('Reached timeout on request to %s' % url)
            return None

    def __repr__(self):
        return '<Poller sensu/%s>' % self.name
