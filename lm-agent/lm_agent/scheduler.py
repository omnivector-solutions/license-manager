from apscheduler.schedulers.asyncio import AsyncIOScheduler

from lm_agent.config import settings


class Scheduler:
    def __init__(self, interval=settings.STAT_INTERVAL):
        self.scheduler = AsyncIOScheduler()
        self.interval = interval

    def add_job(self, func):
        self.scheduler.add_job(func, "interval", seconds=self.interval)

    def start(self):
        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()


scheduler = Scheduler()
