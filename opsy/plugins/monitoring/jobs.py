import asyncio
import random
import time
from flask import current_app
from sqlalchemy.exc import OperationalError
from opsy.app import create_app
from opsy.db import db


def update_cache(zone, config_file):
    with create_app(config_file).app_context():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = zone.get_update_tasks(current_app)
        results = loop.run_until_complete(asyncio.gather(*tasks))
        for del_objects, init_objects in results:
            for i in range(3):  # three retries for deadlocks
                try:
                    for del_object in del_objects:
                        del_object.delete()
                    db.session.bulk_save_objects(init_objects)
                    db.session.commit()
                    break
                except OperationalError as e:  # pylint: disable=invalid-name
                    if i == (3 - 1):
                        raise
                    current_app.logger.info(
                        'Retryable error in transaction on '
                        'attempt %d for zone %s: %s',
                        i + 1, zone.name, e.__class__.__name__)
                    db.session.rollback()  # pylint: disable=no-member
                    time.sleep(random.uniform(.5, 1.5))
