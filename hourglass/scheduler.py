import asyncio
from threading import Thread
from time import sleep


class Scheduler(object):

    def __init__(self, interval, pollers):
        self.loop = asyncio.get_event_loop()
        self.interval = interval
        self.pollers = pollers
        self.loop = asyncio.get_event_loop()
        self._thread_stop = 0
        self._thread = None

    def start(self):
        if not self._thread:
            self._thread = Thread(target=self._run)
            self._thread.start()

    def stop(self):
        self._thread_stop = 1
        self.loop.stop()
        self.loop.close()

    def _run(self):
        if not self._thread_stop:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            self.run_tasks(loop=loop)
            sleep(self.interval)
            self._run()

    def run_tasks(self, loop=None):
        if loop:
            run_loop = loop
        else:
            run_loop = self.loop
        tasks = []
        for poller in self.pollers:
            tasks.append(asyncio.async(asyncio.wait_for(poller.update_cache(), self.interval - 1)))
        run_loop.run_until_complete(asyncio.gather(*tasks))


class UwsgiScheduler(object):

    def __init__(self, interval, pollers):
        self.loop = asyncio.get_event_loop()
        self.interval = interval
        self.pollers = pollers
        self.loop = asyncio.get_event_loop()

    def start(self):
        self.run_tasks()

    def stop(self):
        self.loop.stop()
        self.loop.close()

    def run_tasks(self):
        tasks = []
        for poller in self.pollers:
            tasks.append(asyncio.async(asyncio.wait_for(poller.update_cache(), self.interval - 1)))
        self.loop.run_until_complete(asyncio.gather(*tasks))
