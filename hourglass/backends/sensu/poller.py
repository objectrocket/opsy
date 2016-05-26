from hourglass.backends.sensu.cache import *
from hourglass.backends.poller import Poller
import aiohttp
import asyncio


class SensuPoller(Poller):

    def __init__(self, app, loop, name, config):
        super().__init__(app, loop, name, config)
        self.models = [SensuCheck, SensuClient, SensuEvent, SensuStash]

    @asyncio.coroutine
    def query_api(self, session, uri):
        url = "http://%s:%s/%s" % (self.host, self.port, uri)
        self.app.logger.debug('Making request to %s' % url)
        with aiohttp.Timeout(self.timeout):
            response = yield from session.get(url)
            return (yield from response.json())

    def __repr__(self):
        return '<Poller sensu/%s>' % self.name
