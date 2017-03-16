from opsy.app import create_app, create_scheduler
import asyncio
import uwsgi


config = uwsgi.opt.get('opsy_config', './opsy.ini')
app = create_app(config)
scheduler = create_scheduler(app)
try:
    app.logger.info('Starting the scheduler')
    scheduler.start()
    asyncio.get_event_loop().run_forever()
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
    app.logger.info('Stopping the scheduler')
