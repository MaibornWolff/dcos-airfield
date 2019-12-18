"""Service that handles periodic cleanup tasks like deleting overdue instances"""

from datetime import datetime
from .instance import InstanceService
from .scheduler import SchedulerService
from ..util import dependency_injection as di


class InstanceCleanupService:
    @di.inject
    def __init__(self, instance_service: InstanceService, scheduler: SchedulerService):
        self._instance_service = instance_service
        scheduler.add_job(self._run, 'interval', id='run', minutes=30)

    def _run(self):
        now = datetime.now()
        # Delete instances who have a delete_at time that is elapsed
        for instance in self._instance_service.get_instance_configurations():
            delete_at = instance["configuration"].get("delete_at")
            if not delete_at:
                continue
            delete_at_time = datetime.fromisoformat(delete_at)
            if now >= delete_at_time:
                self._instance_service.delete_instance(instance["instance_id"])
