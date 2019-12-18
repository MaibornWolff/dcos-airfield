import unittest
from unittest import mock
from airfield.configuration.service import ConfigurationService


_configuration = {
    "type": "zeppelin",
    "notebook": {
        "cores": 64,
    },
    "spark": {
        "python_version": "python3",
        "executor_memory": 1024,
        "executor_cores": 1,
    },
    "admin": {
        "group": None,
        "admins": []
    },
    "usermanagement": {
        "enabled": False,
    },
    "libraries": {
        "python": [],
        "r": [],
    },
    "comment": "foobar"
}

_configuration_users = {
    "usermanagement": {
        "enabled": True,
        "users": {
            "admin": None,
            "foo": None
        }
    }
}


class ConfigurationServiceTest(unittest.TestCase):
    def test_prepare_configuration_from_empty(self):
        under_test = ConfigurationService()
        result = under_test.prepare_configuration({})
        self.assertTrue(result is not None)

    def test_prepare_configuration(self):
        under_test = ConfigurationService()
        result = under_test.prepare_configuration(_configuration)
        self.assertEqual(result["type"], "zeppelin")
        self.assertEqual(result["comment"], "foobar")
        self.assertEqual(result["notebook"]["memory"], 1024)
        self.assertEqual(result["notebook"]["cores"], 64)

    def test_prepare_configuration_generate_passwords(self):
        under_test = ConfigurationService()
        result = under_test.prepare_configuration(_configuration_users)
        self.assertTrue(result is not None)
        users = result["usermanagement"]["users"]
        self.assertTrue("admin"in users)
        self.assertTrue("foo"in users)
        self.assertIsNotNone(users["admin"])
        self.assertIsNotNone(users["foo"])


        
