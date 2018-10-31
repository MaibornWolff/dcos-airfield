# -*- coding: utf-8 -*-
"""Wrapper for consul interactions."""

#  standard imports
import json
import logging
from urllib.error import URLError
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
        key = config.CONSUL_BASE_KEY + '/zeppelin_configuration'
        try:
            return json.loads(self.conn.get(key)[key])
        except URLError as e:
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def get_existing_zeppelin_instance_data(self) -> dict:
        key = config.CONSUL_BASE_KEY + '/existing_instances'
        try:
            instance_data = json.loads(self.conn.get(key)[key])
            return instance_data
        except URLError as e:
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def get_zeppelin_default_configuration_data(self):
        key = config.CONSUL_BASE_KEY + '/default_configs'
        try:
            default_configurations = json.loads(self.conn.get(key)[key])
            return default_configurations
        except URLError as e:
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def create_instance_entry(self, instance_data: dict):
        key = config.CONSUL_BASE_KEY + '/existing_instances'
        existing_instances = json.loads(self.conn.get(key)[key])
        existing_instances.append(instance_data)
        try:
            self.conn.put(key, json.dumps(existing_instances))
        except URLError as e:
            logging.error(e)
            error_message = "Consul server cannot be reached."
            self.consul_error_metric.inc()
            raise TechnicalException(error_message)

    def remove_instance_entry(self, instance_id: str):
        key = config.CONSUL_BASE_KEY + '/existing_instances'
        try:
            existing_instances = json.loads(self.conn.get(key)[key])
            for i in range(len(existing_instances)):
                if existing_instances[i][ID_KEY] == instance_id:
                    existing_instances.pop(i)
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
