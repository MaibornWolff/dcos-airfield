# -*- coding: utf-8 -*-
"""Wrapper for consul interactions."""

#  standard imports
import json
import logging
from urllib.error import URLError, HTTPError
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

    def get_zeppelin_configuration(self):
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

    def get_existing_zeppelin_instance_data(self) -> dict:
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
        existing_instances = self.get_existing_zeppelin_instance_data()
        if not existing_instances:
            existing_instances = []
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
