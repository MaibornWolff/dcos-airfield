# -*- coding: utf-8 -*-
"""Handles all interactions with adapters of external services"""

#  standard imports
import json
import logging
from datetime import datetime
# third party imports
from prometheus_client import Counter, Gauge
from apscheduler.schedulers.background import BackgroundScheduler
# custom imports
import config
from . import ZeppelinConfigurationBuilder
from airfield.utility import ApiResponse, ApiResponseStatus
from .adapters import MarathonAdapter, EtcdAdapter, ConsulAdapter, InstanceState
from airfield.utility import TechnicalException

CONSUL_ENTRY_DELETE_AT_KEY = 'delete_at'
CONSUL_ENTRY_ID_KEY = 'id'
CONFIGURATION_KEY = 'configuration'
CONFIGURATION_ID_KEY = 'id'


class AirfieldService(object):
    def __init__(self):
        logging.info('Initializing ZeppelinHubService.')
        logging.debug('Creating background scheduler.')
        self.scheduler = BackgroundScheduler()
        logging.debug('Starting background scheduler.')
        self.scheduler.start()
        self.marathon_adapter = MarathonAdapter()
        if config.ETCD_ENDPOINT:
            self.config_store = EtcdAdapter()
        elif config.CONSUL_ENDPOINT:
            self.config_store = ConsulAdapter()
        else:
            raise Exception("Neither ETCD_ENDPOINT nor CONSUL_ENDPOINT are specified.")
        self.configuration_builder = ZeppelinConfigurationBuilder()
        self._setup_metrics()
        self._start_periodic_tasks()

    def get_zeppelin_instance_status(self, instance_id: str) -> ApiResponse:
        result = ApiResponse()
        instance_status = self.marathon_adapter.get_instance_status(instance_id)
        if instance_status == InstanceState.UNAUTHORIZED or instance_status == InstanceState.CONNECTION_ERROR:
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
        else:
            result.status = ApiResponseStatus.SUCCESS
            result.data = {
                'instance_status': instance_status.name
            }
        return result

    def get_zeppelin_default_configurations(self) -> ApiResponse:
        result = ApiResponse()
        configuration_data = self._get_local_default_configurations()
        result.status = ApiResponseStatus.SUCCESS
        result.data = {
            'configurations': configuration_data
        }
        return result

    def get_existing_zeppelin_instances(self) -> ApiResponse:
        result = ApiResponse()
        try:
            logging.debug('Retrieving existing instances from consul.')
            instance_data = self.config_store.get_existing_zeppelin_instance_data()
            if not instance_data:
                instance_data = []
            result.status = ApiResponseStatus.SUCCESS
            result.data = {
                'instances': instance_data
            }
        except TechnicalException as e:
            logging.error('Error while retrieving existing zeppelin instances. Error={}'.format(e))
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
        return result

    def create_zeppelin_instance(self, custom_settings: dict) -> ApiResponse:
        result = ApiResponse()

        try:
            logging.debug('Loading zeppelin instance base configuration from consul.')
            base_configuration = self._get_zeppelin_base_configuration()
        except TechnicalException as e:
            logging.error('Error while creating zeppelin instance. Error={}'.format(e))
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
            return result

        try:
            logging.debug('Modifying zeppelin instance configuration with custom settings.')
            configuration = self.configuration_builder.create_instance_configuration(
                custom_settings, base_configuration)
        except KeyError as e:
            logging.error('Error while parsing custom settings. Error={}'.format(e))
            logging.debug('Base configuration={}'.format(base_configuration))
            logging.debug('Custom settings={}'.format(custom_settings))
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
            return result

        deployment_successful = self.marathon_adapter.deploy_instance(configuration)
        if deployment_successful:
            logging.info('Create instance successful.')
            try:
                logging.debug('Creating consul entry.')
                instance_data = self.configuration_builder.parse_consul_instance_entry(custom_settings, configuration)
                self.config_store.create_instance_entry(instance_data)
                result.status = ApiResponseStatus.SUCCESS
                self.existing_instances_metric.inc()
                self.active_instances_metric.inc()
                return result
            except TechnicalException as e:
                logging.error('Error while creating consul entry for new zeppelin instance. Error={}'.format(e))
                result.status = ApiResponseStatus.INTERNAL_ERROR
                result.error_message = 'An error occurred.'
                self.error_metric.inc()
                return result
        else:
            logging.error('Create instance failed. Marathon problem encountered.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
            return result

    def delete_zeppelin_instance(self, instance_id: str) -> ApiResponse:
        result = ApiResponse()

        if not self.marathon_adapter.instance_exists(instance_id):
            logging.info('Delete instance failed. ID does not exist.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            return result

        delete_successful = self.marathon_adapter.delete_instance(instance_id)
        if delete_successful:
            logging.info('Delete instance successful.')
            try:
                logging.debug('Removing instance from consul. ID={}'.format(instance_id))
                self.config_store.remove_instance_entry(instance_id)
            except TechnicalException as e:
                logging.error('Could not remove instance entry from consul. Error={}'.format(e))
                self.error_metric.inc()
            result.status = ApiResponseStatus.SUCCESS
            self.active_instances_metric.dec()
            self.existing_instances_metric.dec()
        else:
            logging.info('Delete instance failed.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
        return result

    def restart_zeppelin_instance(self, instance_id: str) -> ApiResponse:
        result = ApiResponse()

        if not self.marathon_adapter.instance_exists(instance_id):
            logging.info('Restart instance failed. ID does not exist.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            return result

        restart_successful = self.marathon_adapter.restart_instance(instance_id)
        if restart_successful:
            logging.info('Restart instance successful.')
            result.status = ApiResponseStatus.SUCCESS
        else:
            logging.info('Restart instance failed.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
        return result

    def start_zeppelin_instance(self, instance_id: str) -> ApiResponse:
        result = ApiResponse()

        if not self.marathon_adapter.instance_exists(instance_id):
            logging.info('Start instance failed. ID does not exist.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            return result

        start_successful = self.marathon_adapter.start_instance(instance_id)
        if start_successful:
            logging.info('Start instance successful.')
            result.status = ApiResponseStatus.SUCCESS
            self.active_instances_metric.inc()
        else:
            logging.info('Start instance failed.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
        return result

    def stop_zeppelin_instance(self, instance_id: str) -> ApiResponse:
        result = ApiResponse()

        if not self.marathon_adapter.instance_exists(instance_id):
            logging.info('Stop Instance failed. ID does not exist.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            return result

        stop_successful = self.marathon_adapter.stop_instance(instance_id)
        if stop_successful:
            logging.info('Stop instance successful.')
            result.status = ApiResponseStatus.SUCCESS
            self.active_instances_metric.dec()
        else:
            logging.info('Stop instance failed.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
        return result

    def _get_zeppelin_base_configuration(self) -> dict:
        configuration = self.config_store.get_zeppelin_configuration()
        if configuration is None:
            logging.info('Zeppelin instance base configuration not found on consul. '
                         'Using local base configuration.')
            configuration = self._get_local_base_configuration()
        return configuration

    def _get_local_default_configurations(self):
        with open(config.LOCAL_ZEPPELIN_DEFAULT_CONFIG_DIRECTORY) as config_file:
            return json.load(config_file)

    def _get_local_base_configuration(self):
        with open(config.LOCAL_ZEPPELIN_BASE_CONFIG_DIRECTORY) as config_file:
            return json.load(config_file)

    def _setup_metrics(self):
        logging.debug('Setting up core service metrics.')
        self.error_metric = Counter('airfield_errors_total',
                                    'AirfieldService Errors')
        self.existing_instances_metric = Gauge('airfield_existing_instances_total',
                                               'Existing Zeppelin Instances')
        self.active_instances_metric = Gauge('airfield_active_instances_total',
                                             'Active Zeppelin Instances')

        try:
            logging.debug('Loading existing instances from consul to initialize metrics.')
            existing_instances = self.config_store.get_existing_zeppelin_instance_data()
            if not existing_instances:
                return
            active_instance_count = 0
            for instance in existing_instances:
                instance_status = self.marathon_adapter.get_instance_status(instance[CONFIGURATION_ID_KEY])
                if instance_status == InstanceState.HEALTHY:
                    active_instance_count += 1

            self.existing_instances_metric.set(len(existing_instances))
            self.active_instances_metric.set(active_instance_count)
        except TechnicalException as e:
            logging.error('Error while loading existing instances from consul. Error={}'.format(e))
            self.error_metric.inc()

    def _start_periodic_tasks(self):
        logging.debug('Starting periodic tasks.')
        logging.debug('Creating `delete_overdue_instances` job.')
        self.scheduler.add_job(self._delete_overdue_instances,
                               'cron',
                               id='id',
                               day_of_week='mon-fri',
                               hour='0-23',
                               minute='*/30')

    def _delete_overdue_instances(self):
        overdue_instances = self._get_overdue_instance_ids()
        if len(overdue_instances) == 0:
            logging.info('No overdue instances found.')
        else:
            logging.info('Deleting {} overdue instances.'.format(len(overdue_instances)))
            for instance_id in overdue_instances:
                logging.info('Deleting {}'.format(instance_id))
                self.delete_zeppelin_instance(instance_id)

    def _get_overdue_instance_ids(self) -> [int]:
        logging.debug('Retrieving existing instances from consul to get overdue instances.')
        overdue_instances = []
        try:
            existing_instances = self.config_store.get_existing_zeppelin_instance_data()
            if not existing_instances:
                return overdue_instances
            for instance in existing_instances:
                delete_at = instance[CONSUL_ENTRY_DELETE_AT_KEY]
                if delete_at and delete_at > datetime.utcnow().timestamp():
                    overdue_instances.append(instance[CONSUL_ENTRY_ID_KEY])
        except TechnicalException as e:
            logging.error('Error while loading existing instances from consul. Error={}'.format(e))
            self.error_metric.inc()
        return overdue_instances
