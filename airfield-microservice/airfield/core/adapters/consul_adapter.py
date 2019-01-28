# -*- coding: utf-8 -*-
"""Wrapper for consul interactions."""

#  standard imports
import json
import logging
import time
from urllib.error import URLError, HTTPError
from uuid import uuid4
# third party imports
from prometheus_client import Counter
from consul_kv import Connection
# custom imports
import config
from airfield.utility import TechnicalException

ID_KEY = 'id'


class ConsulAdapter(object):
    def __init__(self):
        logging.info('Initializing ConsulAdapter')
        self._setup_metrics()
        endpoint = config.CONSUL_ENDPOINT
        self.conn = Connection(endpoint=endpoint)

    def get_zeppelin_marathon_app_definition(self):
        key = config.CONFIG_BASE_KEY + '/zeppelin_configuration'
        try:
            return json.loads(self.conn.get(key)[key])
        except URLError as e:
            if isinstance(e, HTTPError) and e.code == 404:
                return None
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def store_full_backup(self, instance_id, notebooks):
        key = config.CONFIG_BASE_KEY + '/instance_backups/' + instance_id
        try:
            self.conn.put(key, json.dumps(notebooks))
        except URLError as e:
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def retrieve_full_backup(self, instance_id):
        key = config.CONFIG_BASE_KEY + '/instance_backups/' + instance_id
        try:
            return json.loads(self.conn.get(key)[key])
        except URLError as e:
            if isinstance(e, HTTPError) and e.code == 404:
                return []
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def delete_backup(self, instance_id):
        key = config.CONFIG_BASE_KEY + '/instance_backups/' + instance_id
        try:
            self.conn.delete(key)
            return True
        except URLError as e:
            if isinstance(e, HTTPError) and e.code == 404:
                return False
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def get_notebook_index(self):
        key = config.CONFIG_BASE_KEY + '/notebook/index'
        try:
            return json.loads(self.conn.get(key)[key])
        except URLError as e:
            if isinstance(e, HTTPError) and e.code == 404:
                return {}
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def store_notebook(self, notebook, user):
        key = config.CONFIG_BASE_KEY + '/notebook'
        notebook_id = str(uuid4())
        try:
            self.conn.put(key + '/' + notebook_id, json.dumps(notebook))
            index = self.get_notebook_index()
            index[notebook_id] = {
                "created_at": time.time(),
                "name": notebook["name"],
                "id": notebook_id,
                "creator": user
            }
            self.conn.put(key + '/index', json.dumps(index))
        except URLError as e:
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def delete_notebook(self, notebook_id):
        key = config.CONFIG_BASE_KEY + '/notebook'
        index = self.get_notebook_index()
        if notebook_id in index:
            del index[notebook_id]
        else:
            return False
        try:
            self.conn.delete(key + '/' + notebook_id)
            self.conn.put(key + '/index', json.dumps(index))
            return True
        except URLError as e:
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def retrieve_notebook(self, notebook_id):
        key = config.CONFIG_BASE_KEY + '/notebook/' + notebook_id
        try:
            return json.loads(self.conn.get(key)[key])
        except URLError as e:
            if isinstance(e, HTTPError) and e.code == 404:
                return {}
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def get_existing_zeppelin_instances_data(self) -> dict:
        key = config.CONFIG_BASE_KEY + '/existing_instances'
        try:
            instance_data = json.loads(self.conn.get(key)[key])
            return instance_data
        except URLError as e:
            if isinstance(e, HTTPError) and e.code == 404:
                return None
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def get_existing_zeppelin_instance_data(self, instance_id: str):
        instances = self.get_existing_zeppelin_instances_data()
        for instance in instances:
            if instance["id"] == instance_id:
                return instance
        return None

    def get_zeppelin_default_configuration_data(self):
        key = config.CONFIG_BASE_KEY + '/default_configs'
        try:
            default_configurations = json.loads(self.conn.get(key)[key])
            return default_configurations
        except URLError as e:
            if isinstance(e, HTTPError) and e.code == 404:
                return None
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def create_instance_entry(self, instance_data: dict):
        key = config.CONFIG_BASE_KEY + '/existing_instances'
        existing_instances = self.get_existing_zeppelin_instances_data()
        if not existing_instances:
            existing_instances = []
        # check if instance was redeployed - and update entry in that case
        found = False
        for index, instance in enumerate(existing_instances):
            if instance["id"] == instance_data["id"]:
                existing_instances[index] = instance_data
                logging.debug("Updating existing instance in database")
                found = True
                break
        if not found:
            logging.debug("Adding new instance to database")
            existing_instances.append(instance_data)
        try:
            self.conn.put(key, json.dumps(existing_instances))
        except URLError as e:
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def remove_instance_entry(self, instance_id: str):
        key = config.CONFIG_BASE_KEY + '/existing_instances'
        try:
            existing_instances = json.loads(self.conn.get(key)[key])
            instance_index = -1
            for idx, instance in enumerate(existing_instances):
                if instance[ID_KEY] == instance_id:
                    instance_index = idx
            if instance_index > -1:
                existing_instances.pop(instance_index)
            self.conn.put(key, json.dumps(existing_instances))
        except URLError as e:
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def _setup_metrics(self):
        logging.debug('Setting up consul metrics.')
        self.consul_error_metric = Counter('airfield_consul_errors_total',
                                           'ConsulAdapter Errors')
