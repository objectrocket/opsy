from hourglass.backends.sensu.cache import *
from hourglass.backends.poller import Poller
import requests


class SensuPoller(Poller):
    models = [SensuCheck, SensuClient, SensuEvent, SensuStash, SensuResult]

    def __init__(self, app, name, config):
        super().__init__(app, name, config)
        self.models = [SensuCheck, SensuClient, SensuEvent, SensuStash,
                       SensuResult]

    def query_api(self, uri):
        url = "http://%s:%s/%s" % (self.host, self.port, uri)
        self.app.logger.debug('Making request to %s' % url)
        try:
                response = requests.get(url, timeout=self.timeout)
                self.app.logger.debug('Response %s from %s' % (
                    response.status_code, url))
                return response.json()
        except requests.exceptions.Timeout:
            self.app.logger.debug("Reached timeout on request to %s" % url)
            return None

    def __repr__(self):
        return '<Poller sensu/%s>' % self.name
