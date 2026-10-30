from apscheduler import AsyncScheduler
from apscheduler.triggers.interval import IntervalTrigger

from lm_agent.config import settings


class Scheduler:
    def __init__(self, interval=settings.STAT_INTERVAL):
        self._scheduler = AsyncScheduler()
        self.interval = interval

    async def __aenter__(self):
        await self._scheduler.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self._scheduler.__aexit__(*args)

    async def add_job(self, func):
        await self._scheduler.add_schedule(func, IntervalTrigger(seconds=self.interval))

    async def run(self):
        await self._scheduler.run_until_stopped()


scheduler = Scheduler()
