# -*- coding: utf-8 -*-
"""Wrapper for etcd interactions."""

#  standard imports
import json
import logging
from uuid import uuid4
import time
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
        endpoint = config.ETCD_ENDPOINT
        protocol = "http"
        version_prefix = '/v2'
        if "://" in endpoint:
            protocol, endpoint = endpoint.split("://")
        if "/" in endpoint:
            endpoint, version_prefix = endpoint.split("/", 1)
        if ":" not in endpoint:
            host, port = endpoint, 2379
        else:
            host, port = endpoint.split(":")
        self.conn = etcd.Client(host=host, port=int(port), protocol=protocol, version_prefix=version_prefix)

    def get_zeppelin_marathon_app_definition(self):
        key = config.CONFIG_BASE_KEY + '/zeppelin_configuration'
        try:
            return json.loads(self.conn.read(key).value)
        except etcd.EtcdKeyNotFound:
            return None
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def store_full_backup(self, instance_id, notebooks):
        key = config.CONFIG_BASE_KEY + '/instance_backups/' + instance_id
        try:
            self.conn.write(key, json.dumps(notebooks))
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def retrieve_full_backup(self, instance_id):
        key = config.CONFIG_BASE_KEY + '/instance_backups/' + instance_id
        try:
            return json.loads(self.conn.read(key).value)
        except etcd.EtcdKeyNotFound:
            return []
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def delete_backup(self, instance_id):
        key = config.CONFIG_BASE_KEY + '/instance_backups/' + instance_id
        try:
            self.conn.delete(key)
            return True
        except etcd.EtcdKeyNotFound:
            return False
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def get_notebook_index(self):
        key = config.CONFIG_BASE_KEY + '/notebook/index'
        try:
            return json.loads(self.conn.read(key).value)
        except etcd.EtcdKeyNotFound:
            return {}
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def store_notebook(self, notebook, user):
        key = config.CONFIG_BASE_KEY + '/notebook'
        notebook_id = str(uuid4())
        try:
            self.conn.write(key + '/' + notebook_id, json.dumps(notebook))
            index = self.get_notebook_index()
            index[notebook_id] = {
                "created_at": time.time(),
                "name": notebook["name"],
                "id": notebook_id,
                "creator": user
            }
            self.conn.write(key + '/index', json.dumps(index))
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def delete_notebook(self, notebook_id):
        key = config.CONFIG_BASE_KEY + '/notebook'
        index = self.get_notebook_index()
        if notebook_id in index:
            del index[notebook_id]
        else:
            return False
        try:
            self.conn.delete(key + '/' + notebook_id)
            self.conn.write(key + '/index', json.dumps(index))
            return True
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def retrieve_notebook(self, notebook_id):
        key = config.CONFIG_BASE_KEY + '/notebook/' + notebook_id
        try:
            return json.loads(self.conn.read(key).value)
        except etcd.EtcdKeyNotFound:
            return {}
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def get_existing_zeppelin_instances_data(self) -> dict:
        key = config.CONFIG_BASE_KEY + '/existing_instances'
        try:
            return json.loads(self.conn.read(key).value)
        except etcd.EtcdKeyNotFound:
            return None
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def get_existing_zeppelin_instance_data(self, instance_id: str):
        instances = self.get_existing_zeppelin_instances_data()
        for instance in instances:
            if instance["id"] == instance_id:
                return instance
        return None

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
            self.conn.write(key, json.dumps(existing_instances))
        except Exception as e:
            logging.error(e)
            self.etcd_error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def remove_instance_entry(self, instance_id: str):
        key = config.CONFIG_BASE_KEY + '/existing_instances'
        try:
            existing_instances = self.get_existing_zeppelin_instances_data()
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
        logging.debug('Setting up metrics.')
        self.etcd_error_metric = Counter('airfield_etcd_errors_total', 'EtcdAdapter Errors')
