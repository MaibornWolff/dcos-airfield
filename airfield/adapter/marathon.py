"""Handles Marathon interactions"""

import time
from enum import Enum
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from prometheus_client import Counter
from .dcos_auth import retrieve_auth
from ..util.logging import logger

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


MARATHON_URL_POSTFIX = '/service/marathon/v2'


class InstanceState(Enum):
    NOT_FOUND = 0
    UNHEALTHY = 1
    STAGING = 2
    DEPLOYING = 3
    HEALTHY = 4
    STOPPED = 5
    UNAUTHORIZED = 6
    CONNECTION_ERROR = 7


class MarathonAdapter(object):

    def __init__(self):
        logger.info('Initializing MarathonAdapter.')
        self._setup_metrics()
        self.base_url, self.auth = retrieve_auth()

    def get_instance_ip_address_and_port(self, instance_id: str) -> tuple:
        if not instance_id:
            raise Exception("No instance id provided")
        url = self._get_marathon_url() + '/apps/%s/?embed=app.task' % instance_id
        response = requests.get(url=url, auth=self.auth, verify=False)
        try:
            task = response.json()['app'].get("tasks")[0]
            ip_address = task.get("ipAddresses")[0].get("ipAddress")
            port = task.get("ports")[0]
            return ip_address, port
        except KeyError as e:
            logger.error("Failed to get instance ip address and port: %s" % e)
            self.marathon_error_metric.inc()
            return None, None

    def get_instance_status(self, instance_id: str) -> InstanceState:
        if not instance_id:
            raise Exception("No instance id provided")
        url = self._get_marathon_url() + '/apps/%s/?embed=app.counts' % instance_id
        response = requests.get(url=url, auth=self.auth, verify=False)
        if not response.ok:
            logger.error(response.text)
            if response.status_code == 404:
                return InstanceState.NOT_FOUND
            if response.status_code == 401:
                return InstanceState.UNAUTHORIZED
            else:
                self.marathon_error_metric.inc()
                return InstanceState.CONNECTION_ERROR
        try:
            state = response.json()['app']
            if state.get('tasksHealthy') > 0 and state.get('tasksRunning') > 0:
                return InstanceState.HEALTHY
            if state.get('tasksUnhealthy', None) > 0:
                return InstanceState.UNHEALTHY
            if len(state.get('deployments', None)) > 0:
                return InstanceState.DEPLOYING
            if state.get('tasksStaged', None) > 0:
                return InstanceState.STAGING
            else:
                return InstanceState.STOPPED
        except KeyError as e:
            logger.error("Failed to get instance state: %s" % e)
            self.marathon_error_metric.inc()
            return InstanceState.NOT_FOUND

    def get_deployment_status(self, instance_id: str) -> bool:
        if not instance_id:
            raise Exception("No instance id provided")
        url = self._get_marathon_url() + '/apps/%s/tasks' % instance_id
        response = requests.get(url=url, auth=self.auth, verify=False)
        if response.ok:
            return len(response.json()["tasks"]) != 0
        else:
            logger.error(response.text)
            self.marathon_error_metric.inc()
            return False

    def instance_exists(self, instance_id: str) -> bool:
        if instance_id is None:
            logger.info('No instance ID provided for existence check. Aborting search.')
            return False
        return self.get_instance_status(instance_id) != InstanceState.NOT_FOUND

    def deploy_instance(self, instance_definition) -> bool:
        url = self._get_marathon_url() + '/apps?force=true'  # will update an instance definition or create a new one
        response = requests.put(url=url, json=[instance_definition], auth=self.auth, verify=False)
        if not response.ok:
            logger.error(response.text)
            self.marathon_error_metric.inc()
            return False
        return True

    def start_instance(self, instance_id: str) -> bool:
        payload = {
            'id': instance_id,
            'instances': 1
        }
        return self._patch_instance(instance_id, payload)

    def stop_instance(self, instance_id: str) -> bool:
        payload = {
            'id': instance_id,
            'instances': 0
        }
        return self._patch_instance(instance_id, payload)

    def restart_instance(self, instance_id: str) -> bool:
        url = self._get_marathon_url() + '/apps/{}/restart'.format(instance_id)
        response = requests.post(url, auth=self.auth, verify=False)
        if response.ok:
            return True
        else:
            logger.error(response.text)
            self.marathon_error_metric.inc()
            return False

    def delete_instance(self, instance_id: str) -> bool:
        url = self._get_marathon_url() + '/apps/{}'.format(instance_id)
        response = requests.delete(url, auth=self.auth, verify=False)
        if response.ok:
            return True
        else:
            logger.error(response.text)
            self.marathon_error_metric.inc()
            return False

    def _patch_instance(self, instance_id: str, payload: dict) -> bool:
        url = self._get_marathon_url() + '/apps/{}'.format(instance_id)
        logger.info('Patching instance. url={0} id={1}'.format(url, instance_id))
        logger.debug('Patch payload={}'.format(payload))
        response = requests.patch(url, json=payload, auth=self.auth, verify=False)
        if response.ok:
            return True
        else:
            logger.error(response.text)
            self.marathon_error_metric.inc()
            return False

    def _wait_for_deployment(self, instance_id: str) -> bool:
        wait_time = 0
        state = self.get_instance_status(instance_id)
        while state != InstanceState.DEPLOYING and state != InstanceState.HEALTHY:
            if wait_time > 5 * 60:
                logger.error('Deployment did not complete after 5 minutes. id={}'.format(instance_id))
                self.marathon_error_metric.inc()
                return False
            time.sleep(10)
            wait_time += 10
            state = self.get_instance_status(instance_id)
        return True

    def _get_marathon_url(self) -> str:
        return self.base_url + MARATHON_URL_POSTFIX

    def _setup_metrics(self):
        self.marathon_error_metric = Counter('airfield_marathon_errors_total',
                                             'MarathonAdapter Errors')
