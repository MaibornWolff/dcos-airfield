import unittest
from unittest import mock
from airfield.util import dependency_injection as di
from airfield.adapter.marathon import MarathonAdapter
from airfield.adapter.kv import KVAdapter
from airfield.util import logging
from tests.mocks.kv import InMemoryKVAdapter


class AirfieldApiTest(unittest.TestCase):
    def setUp(self):
        logging.silence()
        di.test_setup_clear_registry()
        self.kv_mock = InMemoryKVAdapter()
        di.register(MarathonAdapter, mock.MagicMock())
        di.register(KVAdapter, self.kv_mock)
        from airfield.app import create_app
        self.app = create_app()
        self.client = self.app.test_client()
    
    def test_login_state(self):
        result = self.client.get("/api/security/state")
        data = result.get_json()
        self.assertFalse(data["authentication"])

    def test_security_groups(self):
        result = self.client.get("/api/security/groups")
        data = result.get_json()
        self.assertEqual(data, {'dcos_groups_activated': False, 'groups': [], 'oidc_activated': False})
