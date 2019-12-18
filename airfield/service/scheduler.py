"""Helper service that manages all job schedules"""

from apscheduler.schedulers.background import BackgroundScheduler


class SchedulerService:
    def __init__(self):
        self._scheduler = BackgroundScheduler()
        self._scheduler.start()

    def add_job(self, func, trigger, **kwargs):
        self._scheduler.add_job(func, trigger, **kwargs)
