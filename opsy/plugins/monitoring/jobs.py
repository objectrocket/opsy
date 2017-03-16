import asyncio
import random
import time
from datetime import datetime
from sqlalchemy.exc import OperationalError
from opsy.extensions import db
from opsy.plugins.monitoring.backends.base import Zone
from opsy.plugins.monitoring.exceptions import PollFailure


def update_cache(zone_id, app):
    with app.app_context():
        zone = Zone.query.get(zone_id)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = zone.get_update_tasks(app)
        try:
            results = loop.run_until_complete(asyncio.gather(*tasks))
            for i in range(3):  # three retries for deadlocks
                try:
                    for del_objects, init_objects in results:
                        for del_object in del_objects:
                            del_object.delete()
                        db.session.bulk_save_objects(init_objects)
                    db.session.commit()
                    zone.status = 'ok'
                    zone.last_poll_time = datetime.utcnow()
                    zone.save()
                    app.logger.info('Updated cache for zone %s.', zone.name)
                    break
                except OperationalError as error:
                    if i == (3 - 1):
                        raise
                    app.logger.info(
                        'Retryable error in transaction on '
                        'attempt %d for zone %s: %s',
                        i + 1, zone.name, error.__class__.__name__)
                    db.session.rollback()  # pylint: disable=no-member
                    time.sleep(random.uniform(.5, 1.5))
        except (PollFailure, OperationalError) as error:
            app.logger.error(
                'Failed to update cache on zone %s: %s',
                zone.name, error.__class__.__name__)
            zone.status = 'critical'
            zone.save()
