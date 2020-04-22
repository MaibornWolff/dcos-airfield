import unittest
from unittest import mock
from airfield.util import dependency_injection as di
from airfield.adapter.marathon import MarathonAdapter, InstanceState
from airfield.adapter.kv import KVAdapter
from airfield.util import logging
from tests.mocks.marathon_adapter import MarathonAdapterMock
from tests.mocks.kv import InMemoryKVAdapter
import json


class InstanceApiTest(unittest.TestCase):
    def setUp(self):
        logging.silence()
        di.test_setup_clear_registry()
        self.marathon_adapter_mock = MarathonAdapterMock()
        self.kv_mock = InMemoryKVAdapter()
        di.register(MarathonAdapter, self.marathon_adapter_mock)
        di.register(KVAdapter, self.kv_mock)
        from airfield.app import create_app
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def tearDown(self):
        di.test_setup_clear_registry()

    def test_get_prices(self):
        result = self.client.get("/api/instance_prices")
        data = result.get_json()
        self.assertEqual(data, {
            'cost_tracking_enabled': False,
            'cost_currency': 'EURO',
            'cost_core_per_minute': 0.0,
            'cost_gb_per_minute': 0.0
        })

    def test_calculate_costs(self):
        json_string = json.dumps({
                'spark': {
                    'cores_max': 4,
                    'executor_cores': 1,
                    'executor_memory': 1024
                },
                'notebook': {
                    'cores': 4,
                    'memory': 1024
                }
            })
        result = self.client.get(f"/api/instance_costs?configuration={json_string}")
        data = result.get_json()
        self.assertEqual(data, {'costs_per_hour': 0.0})

    def test_get_instances(self):
        response = self.client.get("/api/instance")
        data = response.get_json()
        self.assertEqual(data, dict(instances=[]))

    def test_create_instance(self):
        self.marathon_adapter_mock.value_get_instance_status(InstanceState.HEALTHY)
        configuration = dict(configuration=dict(comment="foobar", delete_at="2000-01-01", notebook=dict(cores=4)))
        response = self.client.post("/api/instance", json=configuration)
        data = response.get_json()
        self.assertTrue("instance_id" in data)
        instance_id = data["instance_id"]
        app_definition = self.marathon_adapter_mock.value_deploy_instance()
        self.assertEqual(app_definition["cpus"], 4)
        response = self.client.get("/api/instance")
        data = response.get_json()["instances"]
        self.assertTrue(len(data) == 1)
        instance = data[0]
        self.assertEqual(instance_id, instance["instance_id"])
        self.assertEqual("foobar", instance["details"]["comment"])
        self.assertEqual("2000-01-01T00:00:00", instance["details"]["delete_at"])

    def test_get_instance_credentials(self):
        configuration = dict(
            configuration=dict(usermanagement=dict(enabled=True, users=dict(admin="notsecure", random=None))))
        response = self.client.post("/api/instance", json=configuration)
        data = response.get_json()
        self.assertTrue("instance_id" in data)
        instance_id = data["instance_id"]
        response = self.client.get("/api/instance/{}/credentials".format(instance_id))
        credentials = response.get_json()
        self.assertTrue("admin" in credentials)
        self.assertEqual("notsecure", credentials["admin"])
        self.assertTrue("random" in credentials)
        self.assertIsNotNone(credentials["random"])

    def test_delete_instance(self):
        self.marathon_adapter_mock.value_get_instance_status(InstanceState.NOT_FOUND)
        configuration = dict(configuration=dict())
        response = self.client.post("/api/instance", json=configuration)
        data = response.get_json()
        self.assertTrue("instance_id" in data)
        instance_id = data["instance_id"]
        response = self.client.delete("/api/instance/{}".format(instance_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/instance").get_json()["instances"], [])
        data = self.client.get("/api/instance?deleted=true").get_json()["instances"]
        self.assertTrue(len(data) == 1)
        instance = data[0]
        self.assertEqual(instance_id, instance["instance_id"])
        self.assertTrue("deleted_at" in instance["details"])

    def test_update_instance(self):
        self.marathon_adapter_mock.value_get_instance_status(InstanceState.HEALTHY)
        configuration = dict(configuration=dict(admin=dict(group="test")))
        data = self.client.post("/api/instance", json=configuration).get_json()
        self.assertTrue("instance_id" in data)
        instance_id = data["instance_id"]
        configuration["configuration"]["comment"] = "foobar"
        configuration["configuration"]["notebook"] = dict(cores=4)
        configuration["configuration"]["admin"] = dict(group="foobar")
        response = self.client.put("/api/instance/{}".format(instance_id), json=configuration)
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/instance/{}/configuration".format(instance_id)).get_json()
        self.assertEqual(response["comment"], "foobar")
        self.assertEqual(response["notebook"]["cores"], 4)
        self.assertEqual(response["admin"]["group"], "test")
        app_definition = self.marathon_adapter_mock.value_deploy_instance()
        self.assertEqual(app_definition["cpus"], 4)

    def test_restart_instance(self):
        self.marathon_adapter_mock.value_get_instance_status(InstanceState.HEALTHY)
        configuration = dict(configuration=dict())
        instance_id = self.client.post("/api/instance", json=configuration).get_json()["instance_id"]
        response = self.client.post("/api/instance/{}/restart".format(instance_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "restarted")
        self.assertTrue(instance_id in self.marathon_adapter_mock.value_restart_instance())
        self.marathon_adapter_mock.value_get_instance_status(InstanceState.STOPPED)
        response = self.client.post("/api/instance/{}/restart".format(instance_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "started")
        self.assertTrue(instance_id in self.marathon_adapter_mock.value_start_instance())

    def test_stop_instance(self):
        self.marathon_adapter_mock.value_get_instance_status(InstanceState.HEALTHY)
        configuration = dict(configuration=dict())
        instance_id = self.client.post("/api/instance", json=configuration).get_json()["instance_id"]
        response = self.client.post("/api/instance/{}/stop".format(instance_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "stopped")
        self.assertTrue(instance_id in self.marathon_adapter_mock.value_stop_instance())
        self.marathon_adapter_mock.value_get_instance_status(InstanceState.STOPPED)
        response = self.client.post("/api/instance/{}/stop".format(instance_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "")

    def test_start_instance(self):
        self.marathon_adapter_mock.value_get_instance_status(InstanceState.HEALTHY)
        configuration = dict(configuration=dict())
        instance_id = self.client.post("/api/instance", json=configuration).get_json()["instance_id"]
        response = self.client.post("/api/instance/{}/start".format(instance_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "")
        self.marathon_adapter_mock.value_get_instance_status(InstanceState.STOPPED)
        response = self.client.post("/api/instance/{}/start".format(instance_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "started")
        self.assertTrue(instance_id in self.marathon_adapter_mock.value_start_instance())
