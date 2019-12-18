

class SchedulerServiceMock:
    def __init__(self):
        self._jobs = list()
    
    def add_job(self, func, trigger, **kwargs):
        self._jobs.append(func)
    
    def run(self):
        for job in self._jobs:
            job()