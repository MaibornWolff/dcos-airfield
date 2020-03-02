import unittest
from unittest import mock
from airfield.util import dependency_injection as di
from airfield.adapter.marathon import MarathonAdapter, InstanceState
from airfield.adapter.kv import KVAdapter
from airfield.service.notebook_zeppelin import ZeppelinNotebookService
from airfield.service.scheduler import SchedulerService
from airfield.util import logging
from tests.mocks.marathon_adapter import MarathonAdapterMock
from tests.mocks.kv import InMemoryKVAdapter
from tests.mocks.scheduler import SchedulerServiceMock


class NotebookApiTest(unittest.TestCase):
    def setUp(self):
        logging.silence()
        di.test_setup_clear_registry()
        self.marathon_adapter_mock = MarathonAdapterMock()
        self.kv_mock = InMemoryKVAdapter()
        self.zeppelin_instance_mock = mock.MagicMock()
        self.scheduler_mock = SchedulerServiceMock()
        di.register(MarathonAdapter, self.marathon_adapter_mock)
        di.register(KVAdapter, self.kv_mock)
        di.register(ZeppelinNotebookService, self.zeppelin_instance_mock)
        di.register(SchedulerService, self.scheduler_mock)
        from airfield.app import create_app
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def tearDown(self):
        di.test_setup_clear_registry()
    
    def test_get_stored_notebook(self):
        response = self.client.get("/api/notebook")
        data = response.get_json()
        self.assertEqual(data, {"notebooks": []})

    def test_export_notebook(self):
        configuration = dict(configuration=dict())
        instance_id = self.client.post("/api/instance", json=configuration).get_json()["instance_id"]
        self.zeppelin_instance_mock.export_notebook.return_value = ("abcd", {"name": "abcd"})
        response = self.client.post("/api/notebook", json=dict(instance_id=instance_id, notebook_id="abcd"))
        self.assertEqual(response.status_code, 200)
        return response.get_json()["notebook_id"], 200

    def test_delete_notebook(self):
        notebook_id, _ = self.test_export_notebook()
        response = self.client.get("/api/notebook").get_json()
        response = self.client.delete("/api/notebook/{}".format(notebook_id))
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/notebook").get_json()
        self.assertEqual(response, {"notebooks": []})
        
    def test_import_notebook(self):
        configuration = dict(configuration=dict())
        instance_id = self.client.post("/api/instance", json=configuration).get_json()["instance_id"]
        self.zeppelin_instance_mock.export_notebook.return_value = ("abcd", {"name": "abcd"}), 200
        response = self.client.post("/api/notebook", json=dict(instance_id=instance_id, notebook_id="abcd"))
        self.assertEqual(response.status_code, 200)
        self.zeppelin_instance_mock.export_notebook.assert_called_once()
        notebook_id = response.get_json()["notebook_id"]
        response = self.client.post("/api/notebook/{}/import".format(notebook_id), json=dict(instance_id=instance_id))
        self.assertEqual(response.status_code, 200)
        self.zeppelin_instance_mock.import_notebook.assert_called_once()

    def test_get_instance_notebooks(self):
        notebooks = [{"name": "ABCD", "id": "abcd"}, {"name": "FOO", "id": "bar"}]
        self.zeppelin_instance_mock.get_instance_notebooks.return_value = notebooks
        configuration = dict(configuration=dict())
        instance_id = self.client.post("/api/instance", json=configuration).get_json()["instance_id"]
        response = self.client.get("/api/instance/{}/notebook".format(instance_id))
        self.assertEqual(response.get_json()["notebooks"], notebooks)

    def test_backup_restore_notebooks(self):
        notebooks = [{"name": "ABCD", "id": "abcd"}]
        self.zeppelin_instance_mock.is_import_possible.return_value = True
        self.zeppelin_instance_mock.get_instance_notebooks.return_value = notebooks
        self.zeppelin_instance_mock.export_notebook.return_value = ("ABCD", {"name": "ABCD", "id": "abcd", "paragraphs": []})
        configuration = dict(configuration=dict())
        instance_id = self.client.post("/api/instance", json=configuration).get_json()["instance_id"]

        response = self.client.post("/api/instance/{}/notebook/backup".format(instance_id))
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/api/instance/{}/notebook/restore".format(instance_id))
        self.assertEqual(response.status_code, 200)
        self.scheduler_mock.run()
        self.zeppelin_instance_mock.import_notebook.assert_called_once()
    
    def test_cancel_restore_notebooks(self):
        notebooks = [{"name": "ABCD", "id": "abcd"}]
        self.zeppelin_instance_mock.is_import_possible.return_value = True
        self.zeppelin_instance_mock.get_instance_notebooks.return_value = notebooks
        self.zeppelin_instance_mock.export_notebook.return_value = ("ABCD", {"name": "ABCD", "id": "abcd", "paragraphs": []})
        configuration = dict(configuration=dict())
        instance_id = self.client.post("/api/instance", json=configuration).get_json()["instance_id"]

        response = self.client.post("/api/instance/{}/notebook/backup".format(instance_id))
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/api/instance/{}/notebook/restore".format(instance_id))
        self.assertEqual(response.status_code, 200)
        self.client.delete("/api/instance/{}/notebook/restore".format(instance_id))
        self.scheduler_mock.run()
        self.zeppelin_instance_mock.import_notebook.assert_not_called()

  