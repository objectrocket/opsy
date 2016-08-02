from opsy.scheduler import Scheduler
import time
import uwsgi


config = uwsgi.opt.get('opsy_config', './opsy.ini')
scheduler = Scheduler(config)
scheduler.create_cache_db()
while True:
    scheduler.run_tasks()
    time.sleep(scheduler.interval)
