# -*- coding: utf-8 -*-
"""Handles Marathon interactions."""

#  standard imports
import os
import time
import logging
import requests
import subprocess
from enum import Enum
# third party imports
from prometheus_client import Counter
# custom imports
import config
from .dcos_auth import retrieve_auth


DCOS_CLI_TOKEN_SUBPROCESS = ['dcos', 'config', 'show', 'core.dcos_acs_token']
DCOS_CLI_URL_SUBPROCESS = ['dcos', 'config', 'show', 'core.dcos_url']
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
        logging.info('Initializing MarathonAdapter.')
        self._setup_metrics()

    def get_instance_status(self, instance_id: str) -> InstanceState:
        authorization = retrieve_auth()
        url = self._get_marathon_url(authorization[0]) + '/apps/%s/?embed=app.counts' % instance_id
        response = requests.get(
            url=url,
            auth=authorization[1],
            verify=False
        )
        if not response.ok:
            logging.error(response, response.text)
            if response.status_code == 404:
                self.marathon_error_metric.inc()
                return InstanceState.CONNECTION_ERROR
            if response.status_code == 401:
                return InstanceState.UNAUTHORIZED
            else:
                return InstanceState.NOT_FOUND
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
            logging.error(e)
            self.marathon_error_metric.inc()
            return InstanceState.NOT_FOUND

    def instance_exists(self, instance_id: str) -> bool:
        if instance_id is None:
            logging.info('No instance ID provided for existence check. Aborting search.')
            return False
        if self.get_instance_status(instance_id) == InstanceState.NOT_FOUND:
            return False
        else:
            return True

    def deploy_instance(self, instance_definition) -> bool:
        wait_for_deployment = config.WAIT_FOR_DEPLOYMENT
        authorization = retrieve_auth()
        url = self._get_marathon_url(authorization[0]) + '/apps'
        response = requests.put(
            url=url,
            json=[instance_definition],
            auth=authorization[1],
            verify=False
        )
        if not response.ok:
            logging.error(response.text)
            self.marathon_error_metric.inc()
            return False
        if wait_for_deployment:
            logging.info('Wait flag set. Waiting for deployment to complete.')
            self._wait_for_deployment(instance_definition['id'])
        else:
            logging.info('Wait flag not set. Skipping deployment completion wait time.')
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
        authorization = retrieve_auth()
        url = self._get_marathon_url(authorization[0]) + '/apps/{}/restart'.format(instance_id)
        response = requests.post(
            url,
            auth=authorization[1],
            verify=False
        )
        if response.ok:
            return True
        else:
            logging.error(response.text)
            self.marathon_error_metric.inc()
            return False

    def delete_instance(self, instance_id: str) -> bool:
        authorization = retrieve_auth()
        url = self._get_marathon_url(authorization[0]) + '/apps/{}'.format(instance_id)
        response = requests.delete(
            url,
            auth=authorization[1],
            verify=False
        )
        if response.ok:
            return True
        else:
            logging.error(response.text)
            self.marathon_error_metric.inc()
            return False

    def _patch_instance(self, instance_id: str, payload: dict) -> bool:
        authorization = retrieve_auth()
        url = self._get_marathon_url(authorization[0]) + '/apps/{}'.format(instance_id)
        logging.info('Patching instance. url={0} id={1}'.format(url, instance_id))
        logging.debug('Patch payload={}'.format(payload))
        response = requests.patch(
            url,
            json=payload,
            auth=authorization[1],
            verify=False
        )
        if response.ok:
            return True
        else:
            logging.error(response.text)
            self.marathon_error_metric.inc()
            return False

    def _wait_for_deployment(self, instance_id: str) -> bool:
        wait_time = 0
        state = self.get_instance_status(instance_id)
        while state != InstanceState.DEPLOYING and state != InstanceState.HEALTHY:
            if wait_time > 5 * 60:
                logging.error('Deployment did not complete after 5 minutes. id={}'.format(instance_id))
                self.marathon_error_metric.inc()
                return False
            time.sleep(10)
            wait_time += 10
            state = self.get_instance_status(instance_id)
        return True

    def _get_marathon_url(self, base_url) -> str:
        return base_url + MARATHON_URL_POSTFIX

    def _setup_metrics(self):
        self.marathon_error_metric = Counter('airfield_marathon_errors_total',
                                             'MarathonAdapter Errors')