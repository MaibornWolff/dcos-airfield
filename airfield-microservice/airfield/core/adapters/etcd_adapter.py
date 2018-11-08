# -*- coding: utf-8 -*-
"""Wrapper for etcd interactions."""

#  standard imports
import json
import logging
# third party imports
from prometheus_client import Counter
import etcd
# custom imports
import config
from airfield.utility import TechnicalException


ID_KEY = 'id'


class EtcdAdapter(object):
    def __init__(self):
        logging.info('Initializing EtcdAdapter')
        self._setup_metrics()
        if ":" not in config.ETCD_ENDPOINT:
            host, port = config.ETCD_ENDPOINT, 2379
        else:
            host, port = config.ETCD_ENDPOINT.split(":")
        self.conn = etcd.Client(host=host, port=int(port))

    def get_zeppelin_configuration(self):
        key = config.CONFIG_BASE_KEY + '/zeppelin_configuration'
        try:
            return json.loads(self.conn.read(key).value)
        except etcd.EtcdKeyNotFound:
            return None
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def get_existing_zeppelin_instance_data(self) -> dict:
        key = config.CONFIG_BASE_KEY + '/existing_instances'
        try:
            return json.loads(self.conn.read(key).value)
        except etcd.EtcdKeyNotFound:
            return None
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def get_zeppelin_default_configuration_data(self):
        key = config.CONFIG_BASE_KEY + '/default_configs'
        try:
            return json.loads(self.conn.read(key).value)
        except etcd.EtcdKeyNotFound:
            return None
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def create_instance_entry(self, instance_data: dict):
        key = config.CONFIG_BASE_KEY + '/existing_instances'
        existing_instances = self.get_existing_zeppelin_instance_data()
        if not existing_instances:
            existing_instances = []
        existing_instances.append(instance_data)
        try:
            self.conn.write(key, json.dumps(existing_instances))
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def remove_instance_entry(self, instance_id: str):
        key = config.CONFIG_BASE_KEY + '/existing_instances'
        try:
            existing_instances = self.get_existing_zeppelin_instance_data()
            instance_index = -1
            for idx, instance in enumerate(existing_instances):
                if instance[ID_KEY] == instance_id:
                    instance_index = idx
            if instance_index > -1:
                existing_instances.pop(instance_index)
            self.conn.write(key, json.dumps(existing_instances))
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def _setup_metrics(self):
        logging.debug('Setting up consul metrics.')
        self.etcd_error_metric = Counter('airfield_etcd_errors_total', 'EtcdAdapter Errors')
