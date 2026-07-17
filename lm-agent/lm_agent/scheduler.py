import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from lm_agent.config import settings


class Scheduler:
    def __init__(self, interval=settings.STAT_INTERVAL):
        self.interval = interval
        self._scheduler = None

    def add_job(self, func):
        self._scheduler.add_job(func, "interval", seconds=self.interval)

    def start(self, loop: asyncio.AbstractEventLoop):
        """Start the scheduler with the provided event loop."""
        self._scheduler = AsyncIOScheduler(event_loop=loop)
        self._scheduler.start()

    def stop(self):
        if self._scheduler:
            self._scheduler.shutdown()


scheduler = Scheduler()
