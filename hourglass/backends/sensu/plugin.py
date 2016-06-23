import asyncio
from .cache import *
from ..plugin import BasePlugin


class SensuPlugin(BasePlugin):
    zone_model = SensuZone
    zone_metadata = SensuZoneMetadata
    models = [SensuCheck, SensuClient, SensuEvent, SensuStash, SensuResult]

    @asyncio.coroutine
    def query_api(self, session, url):
        with aiohttp.Timeout(self.timeout):
            response = yield from session.get(url)
            return (yield from response.json())

    @asyncio.coroutine
    def update_objects(self, app, loop, model):
        metadata_key = '%s_%s_last_updated' % (self.zone_model.name,
                                               model.__tablename__)
        init_objects = []
        try:
            with aiohttp.ClientSession(loop=loop) as session:
                url = "http://%s:%s/%s" % (self.host, self.port, model.uri)
                app.logger.debug('Making request to %s' % url)
                results = yield from self.query_api(session, url)
        except aiohttp.errors.ClientError as e:
            app.logger.error('Error updating %s cache for %s: %s' % (
                model.__tablename__, self.name, e))
            return init_objects
        model.query.filter(model.zone_name == self.name).delete()
        zone_metadata.query.filter(zone_metadata.key == metadata_key).delete()
        for result in results:
            init_objects.append(model(self.name, result))
        app.logger.info('Updated %s cache for %s' % (
            model.__tablename__, self.name))
        return init_objects
