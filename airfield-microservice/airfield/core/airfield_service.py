# -*- coding: utf-8 -*-
"""Handles all interactions with adapters of external services"""

#  standard imports
import json
import logging
import time
# third party imports

from prometheus_client import Counter, Gauge
from apscheduler.schedulers.background import BackgroundScheduler
# custom imports
import config
from . import ZeppelinConfigurationBuilder, InstanceRunningTypes
from airfield.utility import ApiResponse, ApiResponseStatus
from .adapters import MarathonAdapter, EtcdAdapter, ConsulAdapter, InstanceState, ZeppelinAdapter, ZeppelinException
from airfield.utility import TechnicalException
from .notebook_transfer_thread import NotebookTransferThread


DELETE_AT_KEY = 'delete_at'
CREATE_AT_KEY = 'created_at'
DEPLOYMENT_TIMEOUT = 180  # 3min
ID_KEY = 'id'
CONFIGURATION_KEY = 'configuration'
CONFIGURATION_ID_KEY = 'id'



class AirfieldService(object):
    def __init__(self):
        logging.info('Initializing AirfieldService.')
        logging.debug('Creating background scheduler.')
        self.scheduler = BackgroundScheduler()
        logging.debug('Starting background scheduler.')
        self.scheduler.start()
        self._threads = {}
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

    def get_stored_notebooks(self) -> ApiResponse:
        result = ApiResponse()
        result.status = ApiResponseStatus.SUCCESS
        notebooks = self.config_store.get_notebook_index()
        if notebooks is None:
            result.data = {
                'notebooks': []
            }
        else:
            result.data = {
                'notebooks': list(notebooks.values())
            }
        return result

    def get_instance_notebooks(self, instance_id):
        result = ApiResponse()
        instance = self.config_store.get_existing_zeppelin_instance_data(instance_id)
        if instance is None:
            result.status = ApiResponseStatus.NOT_FOUND
            result.error_message = 'The instance was not found.'
        else:
            if len(instance["configuration"]["users"]) > 0:
                zeppelin = ZeppelinAdapter(instance["url"], instance["configuration"]["users"][0])
            else:
                zeppelin = ZeppelinAdapter(instance["url"])
            notes = zeppelin.list_notebooks().json()
            new_notes = list(filter(lambda x: not (x["name"].startswith("Zeppelin Tutorial") or
                                                   x["name"].startswith("~Trash")), notes["body"]))
            result.status = ApiResponseStatus.SUCCESS
            result.data = {
                'notebooks': new_notes
            }
            return result

    def export_notebook(self, data, username, force):
        result = ApiResponse()
        notebooks = self.config_store.get_notebook_index()
        for notebook in notebooks.values():
            if notebook["creator"] == username and notebook["name"] == data["name"]:
                if force != 'true':
                    result.status = ApiResponseStatus.CONFLICT
                    result.error_message = 'A note with this name from the same user already exists'
                    return result
                else:  # note will be recreated with a new id later
                    self.config_store.delete_notebook(notebook["id"])
                    break

        instance = self.config_store.get_existing_zeppelin_instance_data(data["instanceId"])
        if instance is None:
            result.status = ApiResponseStatus.NOT_FOUND
            result.error_message = 'The instance was not found.'
        else:
            if len(instance["configuration"]["users"]) > 0:
                zeppelin = ZeppelinAdapter(instance["url"], instance["configuration"]["users"][0])
            else:
                zeppelin = ZeppelinAdapter(instance["url"])
            notebook = zeppelin.export_notebook(data["notebookId"])
            self.config_store.store_notebook(notebook, username)
            result.status = ApiResponseStatus.SUCCESS
        return result

    def import_notebook(self, notebook_id, instance_id):
        result = ApiResponse()
        instance = self.config_store.get_existing_zeppelin_instance_data(instance_id)
        if instance is None:
            result.status = ApiResponseStatus.NOT_FOUND
            result.error_message = 'The instance was not found.'
        else:
            if len(instance["configuration"]["users"]) > 0:
                zeppelin = ZeppelinAdapter(instance["url"], instance["configuration"]["users"][0])
            else:
                zeppelin = ZeppelinAdapter(instance["url"])
            notebook = self.config_store.retrieve_notebook(notebook_id)
            if notebook == {}:
                result.status = ApiResponseStatus.NOT_FOUND
                result.error_message = 'The note to be imported was not found.'
            elif notebook is not None:
                zeppelin.import_notebook(notebook)
                result.status = ApiResponseStatus.SUCCESS
            else:
                result.status = ApiResponseStatus.INTERNAL_ERROR
        return result

    def delete_notebook(self, notebook_id):
        result = ApiResponse()
        if self.config_store.delete_notebook(notebook_id):
            result.status = ApiResponseStatus.SUCCESS
        else:
            result.status = ApiResponseStatus.NOT_FOUND
        return result

    def get_zeppelin_instance_status(self, instance_id: str) -> ApiResponse:
        result = ApiResponse()
        marathon_app_id = self._marathon_app_id(instance_id)
        instance_status = self.marathon_adapter.get_instance_status(marathon_app_id)
        if instance_status == InstanceState.UNAUTHORIZED or instance_status == InstanceState.CONNECTION_ERROR:
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
        else:
            result.status = ApiResponseStatus.SUCCESS
            if instance_status == InstanceState.DEPLOYING:
                tasks_running = self.marathon_adapter.get_deployment_status(marathon_app_id)
                stuck_deploying = False
                stuck_duration = 0
                if not tasks_running:
                    instance = self.config_store.get_existing_zeppelin_instance_data(instance_id)
                    now = time.time()
                    if instance is not None and now - instance[CREATE_AT_KEY] > DEPLOYMENT_TIMEOUT:
                        stuck_deploying = True
                        stuck_duration = int((now - instance[CREATE_AT_KEY]) / 60)
                        # stop running thread (if there is one)
                        if instance_id in self._threads:
                            self._threads[instance_id].stop()

                result.data = {
                    'instance_status': instance_status.name,
                    'deployment_stuck': stuck_deploying,
                    'stuck_duration': stuck_duration
                }
            else:
                result.data = {
                    'instance_status': instance_status.name
                }
        return result

    def update_instance_history(self, status_list, instance_id):
        instance = self.config_store.get_existing_zeppelin_instance_data(instance_id)
        if "history" not in instance:
            instance["history"] = self.configuration_builder.create_history_list(status_list, instance)
        else:
            instance["history"].extend(self.configuration_builder.create_history_list(status_list, instance))
        try:
            self.create_or_update_zeppelin_instance(custom_settings=instance, deployment=False)
            logging.info('updating instance history successfully!')
        except:
            logging.error('updating instance history failed!')

    def get_zeppelin_default_configurations(self) -> ApiResponse:
        result = ApiResponse()
        configuration_data = self._get_local_default_configurations()
        for instance_type in configuration_data:
            del instance_type["notebook_templates"]
        result.status = ApiResponseStatus.SUCCESS
        result.data = {
            'configurations': configuration_data
        }
        return result

    def get_existing_zeppelin_instances(self) -> ApiResponse:
        return self.__get_zeppelin_instances(existing=True)

    def get_deleted_zeppelin_instances(self) -> ApiResponse:
        return self.__get_zeppelin_instances(existing=False)

    def __get_zeppelin_instances(self, existing=True) -> ApiResponse:
        result = ApiResponse()
        try:
            if existing:
                logging.debug('Retrieving existing instances.')
                instance_data = self.config_store.get_existing_zeppelin_instances_data()
            else:
                logging.debug('Retrieving deleted instances.')
                instance_data = self.config_store.get_deleted_zeppelin_instances_data()
            if not instance_data:
                instance_data = []
            result.status = ApiResponseStatus.SUCCESS
            result.data = {
                'instances': instance_data
            }
        except TechnicalException as e:
            if existing:
                logging.error('Error while retrieving existing zeppelin instances. Error={}'.format(e))
            else:
                logging.error('Error while retrieving deleted zeppelin instances. Error={}'.format(e))
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
        return result

    def create_or_update_zeppelin_instance(self, custom_settings: dict, previous_id=None, deployment=True, redeploy=False) -> ApiResponse:
        result = ApiResponse()

        if previous_id is not None:
            if previous_id != custom_settings["id"]:
                logging.error("ID from POST does not match GET parameter")
                result.status = ApiResponseStatus.INTERNAL_ERROR
                result.error_message = "ID from POST does not match GET parameter"
                self.error_metric.inc()
                return result
            else:
                # stop potentially running thread for the same id
                if previous_id in self._threads:
                    self._threads[previous_id].stop()
                # backup old notes
                self._backup_all_notes(previous_id)

        app_definition = self._get_zeppelin_marathon_app_definition()

        try:
            logging.debug('Modifying zeppelin instance configuration with custom settings.')
            app_definition, metadata = self.configuration_builder.create_instance_configuration(
                custom_configuration=custom_settings, app_definition=app_definition, redeploy=redeploy)
        except KeyError as e:
            logging.error('Error while parsing custom settings. Error={}'.format(e))
            logging.debug('Base configuration={}'.format(app_definition))
            logging.debug('Custom settings={}'.format(custom_settings))
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
            return result

        if deployment:
            deployment_successful = self.marathon_adapter.deploy_instance(app_definition)
        else:
            deployment_successful = True

        if deployment_successful:
            if deployment:
                logging.info('Create instance successful.')
            try:
                logging.debug('Storing metadata.')
                self.config_store.create_or_update_existing_instance_entry(metadata)
                if deployment:
                    logging.debug('Creating thread to upload notebook templates')
                    #  locate templates for template_id
                    configuration_data = self._get_local_default_configurations()
                    found = False
                    for config_template in configuration_data:
                        if config_template["template_id"] == custom_settings["template_id"]:
                            import_notebooks, _, _ = self._get_notes_backup(
                                previous_id) if previous_id is not None else [], None, None
                            t = NotebookTransferThread(metadata["configuration"]["users"], metadata["url"],
                                                       template_notebooks=config_template["notebook_templates"],
                                                       import_notebooks=import_notebooks)
                            t.start()
                            self._threads[metadata["id"]] = t
                            found = True
                            break
                    if not found:
                        import_notebooks, _, _ = self._get_notes_backup(
                            previous_id) if previous_id is not None else [], None, None
                        t = NotebookTransferThread(metadata["configuration"]["users"], metadata["url"],
                                                   template_notebooks=[],
                                                   import_notebooks=import_notebooks)
                        t.start()
                        self._threads[metadata["id"]] = t

                result.status = ApiResponseStatus.SUCCESS
                self.existing_instances_metric.inc()
                self.active_instances_metric.inc()
                return result
            except TechnicalException as e:
                logging.error('Error while storing metadata for new zeppelin instance. Error={}'.format(e))
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

    def delete_existing_zeppelin_instance(self, instance_id: str) -> ApiResponse:
        result = ApiResponse()
        if instance_id in self._threads:  # stop potentially running notebook_templates thread
            self._threads[instance_id].stop()
        app_id = self._marathon_app_id(instance_id)

        if not self.marathon_adapter.instance_exists(app_id):
            logging.info('Delete instance failed. ID does not exist.')
            result.status = ApiResponseStatus.NOT_FOUND
            result.error_message = 'An error occurred.'
            return result

        delete_successful = self.marathon_adapter.delete_instance(app_id)
        if delete_successful:
            logging.info('Delete instance successful.')
            try:
                logging.debug('Removing instance metadata and storing to the deleted instances. ID={}'.format(instance_id))
                instance = self.config_store.get_existing_zeppelin_instance_data(instance_id)
                instance["deleted_at"] = time.time()
                self.config_store.create_or_update_deleted_instance_entry(instance)
                self.config_store.remove_existing_instance_entry(instance_id)
            except TechnicalException as e:
                logging.error('Could not remove instance metadata. Error={}'.format(e))
                self.error_metric.inc()
            result.status = ApiResponseStatus.SUCCESS
            self.active_instances_metric.dec()
            self.existing_instances_metric.dec()
        else:
            logging.info('Delete instance failed.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
        return result

    def delete_deleted_zeppelin_instance(self, instance_id: str) -> ApiResponse:
        result = ApiResponse()
        try:
            logging.debug('Removing instance metadata from the deleted instances. ID={}'.format(instance_id))
            self.config_store.remove_deleted_instance_entry(instance_id)
        except TechnicalException as e:
            logging.error('Could not remove instance metadata. Error={}'.format(e))
            self.error_metric.inc()
        result.status = ApiResponseStatus.SUCCESS
        self.active_instances_metric.dec()
        self.existing_instances_metric.dec()
        return result

    def restart_zeppelin_instance(self, instance_id: str) -> ApiResponse:
        result = ApiResponse()
        app_id = self._marathon_app_id(instance_id)

        if not self.marathon_adapter.instance_exists(app_id):
            logging.info('Restart instance failed. ID does not exist.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            return result

        self._backup_all_notes(instance_id)
        restart_successful = self.marathon_adapter.restart_instance(app_id)
        if restart_successful:
            logging.info('Restart instance successful.')
            result.status = ApiResponseStatus.SUCCESS
            notes, users, url = self._get_notes_backup(instance_id)
            t = NotebookTransferThread(users, url,
                                       template_notebooks=[],
                                       import_notebooks=notes)
            t.start()
            self._threads[instance_id] = t
            self.update_instance_history(InstanceRunningTypes.RUNNING.name, instance_id)
        else:
            logging.info('Restart instance failed.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
        return result

    def start_zeppelin_instance(self, instance_id: str) -> ApiResponse:
        result = ApiResponse()
        app_id = self._marathon_app_id(instance_id)

        if not self.marathon_adapter.instance_exists(app_id):
            logging.info('Start instance failed. ID does not exist.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            return result

        start_successful = self.marathon_adapter.start_instance(app_id)
        if start_successful:
            notes, users, url = self._get_notes_backup(instance_id)
            t = NotebookTransferThread(users, url,
                                       template_notebooks=[],
                                       import_notebooks=notes)
            t.start()
            self._threads[instance_id] = t
            logging.info('Start instance successful.')
            result.status = ApiResponseStatus.SUCCESS
            self.active_instances_metric.inc()
            self.update_instance_history(InstanceRunningTypes.RUNNING.name, instance_id)
        else:
            logging.info('Start instance failed.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
        return result

    def stop_zeppelin_instance(self, instance_id: str) -> ApiResponse:
        result = ApiResponse()
        app_id = self._marathon_app_id(instance_id)

        if not self.marathon_adapter.instance_exists(app_id):
            logging.info('Stop Instance failed. ID does not exist.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            return result

        self._backup_all_notes(instance_id)
        stop_successful = self.marathon_adapter.stop_instance(app_id)
        if stop_successful:
            logging.info('Stop instance successful.')
            result.status = ApiResponseStatus.SUCCESS
            self.active_instances_metric.dec()
            self.update_instance_history(InstanceRunningTypes.STOPPED.name, instance_id)
        else:
            logging.info('Stop instance failed.')
            result.status = ApiResponseStatus.INTERNAL_ERROR
            result.error_message = 'An error occurred.'
            self.error_metric.inc()
        return result

    def _backup_all_notes(self, instance_id):
        instance = self.config_store.get_existing_zeppelin_instance_data(instance_id)
        if instance is None:
            return False
        else:
            try:
                if len(instance["configuration"]["users"]) > 0:
                    zeppelin = ZeppelinAdapter(instance["url"], instance["configuration"]["users"][0])
                else:
                    zeppelin = ZeppelinAdapter(instance["url"])
                notes = zeppelin.list_notebooks().json()
                user_created_notes = list(filter(lambda x: not (x["name"].startswith("Zeppelin Tutorial") or
                                                                x["name"].startswith("~Trash")), notes["body"]))
                notes_contents = []
                for note in user_created_notes:
                    notes_contents.append(zeppelin.export_notebook(note["id"]))
                self.config_store.store_full_backup(instance_id=instance_id, notebooks=notes_contents)
            except ZeppelinException:
                logging.error("Could not backup notes from instance " + instance_id)

    def _get_notes_backup(self, instance_id):
        instance = self.config_store.get_existing_zeppelin_instance_data(instance_id)
        if instance is None:
            return [], [], ""
        else:
            try:
                # get stored notebooks first
                stored_notes = self.config_store.retrieve_full_backup(instance_id)
                self.config_store.delete_backup(instance_id)
                return stored_notes, instance["configuration"]["users"], instance["url"]
            except ZeppelinException:
                logging.error("Could not fetch notebook backups of instance " + instance_id)

    def _get_zeppelin_marathon_app_definition(self) -> dict:
        app_definition = None
        try:
            app_definition = self.config_store.get_zeppelin_marathon_app_definition()
        except Exception as e:
            logging.warning("Encountered exception when accessing etcd/consul: ", e)
        if app_definition is None:
            logging.info('Zeppelin marathon app definition not found in etcd/consul. '
                         'Using default.')
            with open(config.MARATHON_APP_DEFINITION_FILE) as marathon_file:
                app_definition = json.load(marathon_file)
        if config.HDFS_CONFIG_FOLDER != "":
            hdfs_folder = config.HDFS_CONFIG_FOLDER
            if "://" not in hdfs_folder:
                hdfs_folder = "http://" + hdfs_folder
            app_definition["fetch"] = [{
                "uri": hdfs_folder + "/hdfs-site.xml",
                "extract": False,
                "executable": False,
                "cache": False
            }, {
                "uri": hdfs_folder + "/core-site.xml",
                "extract": False,
                "executable": False,
                "cache": False
            }]

        return app_definition

    def _get_local_default_configurations(self):
        with open(config.LOCAL_ZEPPELIN_DEFAULT_CONFIG_DIRECTORY) as config_file:
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
            logging.debug('Loading existing instances to initialize metrics.')
            existing_instances = self.config_store.get_existing_zeppelin_instances_data()
            if not existing_instances:
                return
            active_instance_count = 0
            for instance in existing_instances:
                instance_status = self.marathon_adapter.get_instance_status(
                    self._marathon_app_id(instance[CONFIGURATION_ID_KEY]))
                if instance_status == InstanceState.HEALTHY:
                    active_instance_count += 1

            self.existing_instances_metric.set(len(existing_instances))
            self.active_instances_metric.set(active_instance_count)
        except TechnicalException as e:
            logging.error('Error while loading existing instances. Error={}'.format(e))
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
                self.delete_existing_zeppelin_instance(instance_id)

    def _get_overdue_instance_ids(self) -> [int]:
        logging.debug('Retrieving existing instances to get overdue instances.')
        overdue_instances = []
        try:
            existing_instances = self.config_store.get_existing_zeppelin_instances_data()
            if not existing_instances:
                return overdue_instances
            for instance in existing_instances:
                if DELETE_AT_KEY in instance:
                    delete_at = instance[DELETE_AT_KEY]
                else:
                    delete_at = None
                if delete_at and delete_at > time.time():
                    overdue_instances.append(instance[ID_KEY])
        except TechnicalException as e:
            logging.error('Error while loading existing instances. Error={}'.format(e))
            self.error_metric.inc()
        return overdue_instances

    def _marathon_app_id(self, instance_id: str):
        if config.MARATHON_APP_GROUP:
            return "%s/%s" % (config.MARATHON_APP_GROUP, instance_id)
        else:
            return instance_id
