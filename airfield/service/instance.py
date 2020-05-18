"""Service to manage zeppelin/jupyter instances"""

from datetime import datetime, timedelta
import random
import string
from ..storage.instance import InstanceStore
from ..adapter.marathon import MarathonAdapter, InstanceState
from .instance_zeppelin import ZeppelinInstanceService
from ..configuration.service import ConfigurationService
from ..settings import config
from ..util import dependency_injection as di
from ..util import metrics
from ..util.logging import logger
from ..api.auth import get_airfield_groups, get_user_groups
from ..util.exception import ConfigurationException, InstanceRunningTimeException


class InstanceService:
    @di.inject
    def __init__(self, zeppelin_instance: ZeppelinInstanceService, configuration_service: ConfigurationService,
                 instance_store: InstanceStore, marathon_adapter: MarathonAdapter):
        self._zeppelin_instance_service = zeppelin_instance
        self._configuration_service = configuration_service
        self._instance_store = instance_store
        self._marathon_adapter = marathon_adapter

    @metrics.instrument
    def get_instances(self, deleted=False):
        instances = list()
        instance_ids = self._instance_store.get_instance_ids(deleted=deleted)
        for instance_id in instance_ids:
            status = self.get_instance(instance_id, deleted=deleted)
            if status != {}:
                instances.append(status)
        return dict(instances=instances)

    @metrics.instrument
    def get_instance(self, instance_id, deleted=False):
        instance_configuration = self._instance_store.get_instance(instance_id, deleted=deleted)
        if not instance_configuration:
            return {}
        instance = self.get_instance_state(instance_id, instance_configuration=instance_configuration, deleted=deleted)
        instance["details"] = self._calculate_instance_details(instance_configuration)
        instance["proxy_url"] = "/proxy/{}".format(instance_id)
        return instance

    @metrics.instrument
    def get_instance_state(self, instance_id, instance_configuration=None, deleted=False):
        if instance_configuration is None:
            instance_configuration = self._instance_store.get_instance(instance_id, deleted=deleted)
        status = InstanceState.DELETED if deleted else self._marathon_adapter.get_instance_status(
            _instance_path(instance_configuration["configuration"], instance_id))
        stuck_deploying = False
        stuck_duration_seconds = 0
        if status == InstanceState.DEPLOYING:
            runtimes = instance_configuration["runtimes"]
            if runtimes and runtimes[-1]["stopped_at"] is None:
                started_at = datetime.fromtimestamp(runtimes[-1]["started_at"])
                if started_at + timedelta(seconds=10 * 60) <= datetime.now():
                    stuck_deploying = True
                    stuck_duration_seconds = (datetime.now() - started_at).seconds
        return {
            "instance_id": instance_id,
            "status": status.name,
            "deployment_stuck": stuck_deploying,
            "stuck_duration": stuck_duration_seconds
        }

    @metrics.instrument
    def get_instance_configuration(self, instance_id):
        instance_configuration = self._instance_store.get_instance(instance_id)
        return instance_configuration["configuration"]

    @metrics.instrument
    def get_instance_admins(self, instance_id):
        data = self._instance_store.get_instance(instance_id)
        return data["configuration"]["admin"]["admins"] + [data["metadata"]["created_by"]]

    @metrics.instrument
    def get_instance_url(self, instance_id):
        instance_configuration = self._instance_store.get_instance(instance_id)["configuration"]
        instance_path = _instance_path(instance_configuration, instance_id)
        ip, port = self._marathon_adapter.get_instance_ip_address_and_port(instance_path)
        if ip is not None and port is not None:
            return "{}:{}".format(ip, port)
        else:
            logger.error('Error while retrieving the ip address and the port of the instance {}'.format(instance_id))
            return None

    @metrics.instrument
    def get_instance_credentials(self, instance_id):
        instance_configuration = self._instance_store.get_instance(instance_id)["configuration"]
        if not instance_configuration["usermanagement"]["enabled"]:
            return []
        if instance_configuration["type"] == "zeppelin":
            return instance_configuration["usermanagement"]["users"]
        elif instance_configuration["type"] == "jupyter":
            return instance_configuration["usermanagement"]["password"]
        else:
            raise Exception("Unknown instance type: {}".format(instance_configuration["type"]))

    @metrics.instrument
    def get_instance_configurations(self):
        instances = list()
        instance_ids = self._instance_store.get_instance_ids()
        for instance_id in instance_ids:
            instance_configuration = self._instance_store.get_instance(instance_id)
            instances.append(dict(instance_id=instance_id, configuration=instance_configuration))
        return instances

    @metrics.instrument
    def create_instance(self, configuration, username):
        configuration = self._configuration_service.prepare_configuration(configuration)
        if config.OIDC_ACTIVATED and config.DCOS_GROUPS_ENABLED:
            group = configuration['admin']['group']
            if not group:
                raise ConfigurationException("No group is selected! Please select a group to deploy the instance!")
            if group not in get_user_groups():
                raise ConfigurationException(f"The user \"{username}\" is not authorized to deploy an instance in the group \"{group}\"!")
            if group not in get_airfield_groups():
                raise ConfigurationException(f"The group \"{group}\" is not available in airfield!")
        instance_id = _generate_instance_id()
        instance_path = _instance_path(configuration, instance_id)
        metadata = dict(created_by=username, created_at=datetime.now().timestamp())
        self._zeppelin_instance_service.create_instance(instance_path, configuration)
        configuration = self._instance_store.insert_instance(instance_id, configuration, metadata)
        self._start_runtime(instance_id, self._calculate_cost_factors(configuration))
        return instance_id

    @metrics.instrument
    def update_instance(self, instance_id, configuration):
        # The DCOS group of the instance is unchangeable, so we fetch the group from the already stored configuration.
        configuration["admin"]["group"] = self.get_instance_configuration(instance_id)["admin"]["group"]
        instance_path = _instance_path(configuration, instance_id)
        configuration = self._configuration_service.prepare_configuration(configuration)
        if self._marathon_adapter.get_instance_status(instance_path) != InstanceState.STOPPED:
            self._finish_runtime(instance_id)
        self._zeppelin_instance_service.update_instance(instance_path, configuration)
        configuration = self._instance_store.update_instance_configuration(instance_id, configuration)
        self._start_runtime(instance_id, self._calculate_cost_factors(configuration))
        return instance_id

    @metrics.instrument
    def delete_instance(self, instance_id):
        instance_configuration = self._instance_store.get_instance(instance_id)["configuration"]
        self._zeppelin_instance_service.delete_instance(_instance_path(instance_configuration, instance_id))
        # We do not check the status here, so the last runtime is always finished.
        self._finish_runtime(instance_id)
        self._add_deleted_at(instance_id)
        self._instance_store.delete_instance(instance_id)

    @metrics.instrument
    def start_instance(self, instance_id):
        instance_configuration = self._instance_store.get_instance(instance_id)
        instance_path = _instance_path(instance_configuration["configuration"], instance_id)
        if self._marathon_adapter.get_instance_status(instance_path) == InstanceState.STOPPED:
            self._marathon_adapter.start_instance(instance_path)
            self._start_runtime(instance_id, self._calculate_cost_factors(instance_configuration))
            return "started"
        return ""

    @metrics.instrument
    def stop_instance(self, instance_id):
        instance_configuration = self._instance_store.get_instance(instance_id)["configuration"]
        instance_path = _instance_path(instance_configuration, instance_id)
        if self._marathon_adapter.get_instance_status(instance_path) != InstanceState.STOPPED:
            self._marathon_adapter.stop_instance(instance_path)
            self._finish_runtime(instance_id)
            return "stopped"
        return ""

    @metrics.instrument
    def restart_instance(self, instance_id):
        instance_configuration = self._instance_store.get_instance(instance_id)
        instance_path = _instance_path(instance_configuration["configuration"], instance_id)
        if self._marathon_adapter.get_instance_status(instance_path) == InstanceState.STOPPED:
            self.start_instance(instance_id)
            return "started"
        self._marathon_adapter.restart_instance(instance_path)
        self._finish_runtime(instance_id)
        self._start_runtime(instance_id, self._calculate_cost_factors(instance_configuration))
        return "restarted"

    @metrics.instrument
    def get_default_configurations(self):
        return dict(configurations=self._configuration_service.get_available_configurations())

    def _calculate_cost_factors(self, instance_configuration):
        configuration = instance_configuration["configuration"]
        num_executors = int(configuration["spark"]["cores_max"]) / int(configuration["spark"]["executor_cores"])
        cores = int(configuration["notebook"]["cores"]) + num_executors * int(configuration["spark"]["executor_cores"])
        memory = int(configuration["notebook"]["memory"]) + num_executors * int(
            configuration["spark"]["executor_memory"])
        return dict(cores=cores, memory=memory)

    def _calculate_instance_details(self, instance_configuration):
        configuration = instance_configuration["configuration"]
        metadata = instance_configuration["metadata"]
        runtimes = instance_configuration["runtimes"]
        if runtimes and runtimes[-1]["stopped_at"] is None:
            started_at = datetime.fromtimestamp(runtimes[-1]["started_at"]).isoformat()
        else:
            started_at = None
        details = dict()
        details["comment"] = configuration["comment"]
        details["created_by"] = metadata["created_by"]
        for key in ["created_at", "deleted_at"]:
            if key in metadata:  # always true for "created_at"
                details[key] = datetime.fromtimestamp(metadata[key]).isoformat()
        details["running_since"] = started_at
        if config.COST_TRACKING_ENABLED:
            details["costs"] = _calculate_costs(instance_configuration)
        if configuration["delete_at"]:
            details["delete_at"] = datetime.fromtimestamp(configuration["delete_at"]).isoformat()
        return details

    def calculate_costs_per_hour(self, configuration):
        now = datetime.now().timestamp()
        instance_configuration = dict(configuration=configuration)
        cost_factors = self._calculate_cost_factors(dict(instance_configuration))
        cost_factors['started_at'] = now
        cost_factors['stopped_at'] = now + 3600

        instance_configuration['runtimes'] = [cost_factors]
        return dict(costs_per_hour=_calculate_costs(instance_configuration)['cost'])

    def _add_deleted_at(self, instance_id):
        metadata = self._instance_store.get_instance(instance_id, deleted=False)["metadata"]
        metadata["deleted_at"] = datetime.now().timestamp()
        self._instance_store.update_instance_metadata(instance_id, metadata)

    def _finish_runtime(self, instance_id):
        try:
            self._instance_store.finish_runtime(instance_id)
        except InstanceRunningTimeException as e:
            logger.debug(e)

    def _start_runtime(self, instance_id, cost_factors):
        try:
            self._instance_store.start_runtime(instance_id, cost_factors)
        except InstanceRunningTimeException as e:
            logger.debug(e)
            self._instance_store.finish_runtime(instance_id)
            self._instance_store.start_runtime(instance_id, cost_factors)


def _calculate_costs(instance_configuration):
    core_minutes = 0.0
    gb_minutes = 0.0
    running_time_seconds = 0
    for runtime in instance_configuration["runtimes"]:
        started_at = datetime.fromtimestamp(runtime["started_at"])
        stopped_at = datetime.fromtimestamp(runtime["stopped_at"]) if runtime["stopped_at"] else datetime.now()
        minutes = (stopped_at - started_at).seconds / 60
        running_time_seconds += (stopped_at - started_at).seconds
        core_minutes += runtime["cores"] * minutes
        gb_minutes += runtime["memory"] / 1024 * minutes
    cost = config.COST_CORE_PER_MINUTE * core_minutes + config.COST_GB_PER_MINUTE * gb_minutes
    return dict(cost=cost, running_time_seconds=running_time_seconds)


def _generate_instance_id() -> str:
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(9))


def _instance_path(configuration, instance_id):
    if configuration["admin"]["group"]:
           return "{}/{}".format(config.DCOS_GROUPS_MAPPING.get(configuration["admin"]["group"]), instance_id)
    else:
        return "{}/{}".format(config.MARATHON_APP_GROUP, instance_id)
