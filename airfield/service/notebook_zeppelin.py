"""Service to manage notebooks in zeppelin instances"""

from .instance import InstanceService
from ..util import dependency_injection as di
from ..util import metrics
from ..adapter.zeppelin import ZeppelinAdapter


class ZeppelinNotebookService:
    @di.inject
    def __init__(self, instance_service: InstanceService):
        self._instance_service = instance_service

    @metrics.instrument
    def get_instance_notebooks(self, instance_id):
        zeppelin = self._adapter(instance_id)
        notebooks = zeppelin.list_notebooks()
        return _filter_notebooks(notebooks)

    @metrics.instrument
    def export_notebook(self, instance_id, notebook_name):
        zeppelin = self._adapter(instance_id)
        notebook = zeppelin.export_notebook(notebook_name)
        return notebook["name"], notebook

    @metrics.instrument
    def import_notebook(self, instance_id, notebook_data):
        zeppelin = self._adapter(instance_id)
        zeppelin.import_notebook(notebook_data)
        return True

    @metrics.instrument
    def is_import_possible(self, instance_id):
        zeppelin = self._adapter(instance_id)
        return zeppelin.ping()

    def _adapter(self, instance_id):
        url = self._instance_service.get_instance_url(instance_id)
        credentials = self._instance_service.get_instance_credentials(instance_id)
        zeppelin = ZeppelinAdapter("http://{}".format(url))
        if credentials:
            username = credentials.keys()[0]
            zeppelin.login(username, credentials[username])
        return zeppelin


def _filter_notebooks(notebooks):
    return list(filter(lambda x: not (x["name"].startswith("Zeppelin Tutorial") or x["name"].startswith("~Trash")), notebooks))