"""Service to manage notebooks in zeppelin/jupyter instances"""

from datetime import datetime, timedelta
from uuid import uuid4
from ..storage.notebook import NotebookStore
from ..storage.instance import InstanceStore
from .notebook_zeppelin import ZeppelinNotebookService
from .scheduler import SchedulerService
from ..configuration.service import ConfigurationService
from ..util import dependency_injection as di
from ..util import metrics
from ..util.logging import logger
from ..util.exception import ConflictError


class NotebookService:
    @di.inject
    def __init__(self, notebook_store: NotebookStore, instance_store: InstanceStore, zeppelin_notebook_service: ZeppelinNotebookService, configuration_service: ConfigurationService, scheduler: SchedulerService):
        self._notebook_store = notebook_store
        self._instance_store = instance_store
        self._zeppelin_notebook_service = zeppelin_notebook_service
        self._configuration_service = configuration_service
        self._schedule_import_list = dict()
        scheduler.add_job(self._run_job, 'interval', id='notebook_import', seconds=20)

    @metrics.instrument
    def get_stored_notebooks(self):
        return dict(notebooks=self._notebook_store.get_notebooks())

    @metrics.instrument
    def delete_stored_notebook(self, notebook_id):
        return self._notebook_store.delete_notebook(notebook_id)

    @metrics.instrument
    def get_instance_notebooks(self, instance_id):
        return dict(notebooks=self._zeppelin_notebook_service.get_instance_notebooks(instance_id))

    @metrics.instrument
    def export_notebook(self, instance_id, notebook_name, username, force):
        notebook_id = self._notebook_store.find_notebook("zeppelin", notebook_name)
        if not notebook_id:
            notebook_id = _gen_notebook_id()
        else:
            if not force:
                raise ConflictError(f"The notebook {notebook_id} already exists!")
        name, notebook_data = self._zeppelin_notebook_service.export_notebook(instance_id, notebook_name)
        self._notebook_store.store_notebook(notebook_id, name, notebook_data, username)
        return notebook_id

    @metrics.instrument
    def import_notebook(self, instance_id, notebook_id):
        notebook = self._notebook_store.get_notebook(notebook_id)
        return self._zeppelin_notebook_service.import_notebook(instance_id, notebook["data"])

    @metrics.instrument
    def backup_notebooks(self, instance_id):
        notebooks = list()
        for notebook in self._zeppelin_notebook_service.get_instance_notebooks(instance_id):
            _, notebook = self._zeppelin_notebook_service.export_notebook(instance_id, notebook["id"])
            notebooks.append(notebook)
        self._instance_store.store_extra_data(instance_id, "notebooks", notebooks)

    @metrics.instrument
    def restore_notebooks(self, instance_id):
        self._schedule_import_list[instance_id] = datetime.now()

    @metrics.instrument
    def cancel_restore_notebooks(self, instance_id):
        self._schedule_import_list.pop(instance_id, None)

    @metrics.instrument
    def get_notebook_templates(self):
        return self._configuration_service.get_available_notebook_templates()

    @metrics.instrument
    def import_notebook_template(self, instance_id, template_id):
        template = self._configuration_service.get_notebook_template(template_id)
        if template:
            self._instance_store.store_extra_data(instance_id, "notebooks", template["notebooks"])
            self.restore_notebooks(instance_id)
        else:
            logger.warning("Requested notebook template {} not found. Not starting import for instance {}".format(template_id, instance_id))

    @metrics.instrument
    def _run_job(self):
        for instance_id in list(self._schedule_import_list.keys()):
            try:
                if self._zeppelin_notebook_service.is_import_possible(instance_id):
                    for notebook in self._instance_store.get_extra_data(instance_id, "notebooks"):
                        self._zeppelin_notebook_service.import_notebook(instance_id, notebook)
                    self._instance_store.delete_extra_data(instance_id, "notebooks")
                    self._schedule_import_list.pop(instance_id, None)
            except Exception as ex:
                logger.exception("Failed to run import job", exc_info=ex)
        for instance_id, time_added in list(self._schedule_import_list.items()):
            if datetime.now() > time_added + timedelta(seconds=60*10):
                logger.warning("Notebook import timed out: {}".format(instance_id))
                self._schedule_import_list.pop(instance_id, None)


def _gen_notebook_id():
    return str(uuid4())