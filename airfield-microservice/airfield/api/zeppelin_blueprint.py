# -*- coding: utf-8 -*-
"""API routes for zeppelin interactions."""

#  standard imports
import logging
# third party imports
from flask import Blueprint, request, Response
from prometheus_client import generate_latest, Counter
# custom imports
from airfield.utility.serialization_utilities import clean_input_string
from airfield.utility import ApiResponseStatus
from airfield.core import airfield_service, UserService, AuthService


ZeppelinBlueprint = Blueprint('zeppelin', __name__)
airfield_requests_metrics = Counter('airfield_requests_total', 'HTTP Requests', ['endpoint', 'method'])


@ZeppelinBlueprint.route('/instance/<instance_id>/state', methods=['GET'])  # get states
@UserService.login_if_oidc
def get_zeppelin_server_state(instance_id):
    instance_id = clean_input_string(instance_id)
    response = airfield_service.get_zeppelin_instance_status(instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/state/', method="GET").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/configurations', methods=['GET'])  # get default configurations
@UserService.login_if_oidc
def get_zeppelin_default_configurations():
    response = airfield_service.get_zeppelin_default_configurations()
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/configurations/', method="GET").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/groups', methods=['GET'])  # get the zeppelin groups for the DCOS cluster
@UserService.login_if_oidc
def get_zeppelin_groups():
    response = airfield_service.get_zeppelin_groups()
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/groups/', method="GET").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance', methods=['GET'])  # get all
@UserService.login_if_oidc
def get_zeppelin_instances():
    response = airfield_service.get_existing_zeppelin_instances_api()
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance', method="GET").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/deleted/instance', methods=['GET'])  # get all deleted instances
@UserService.login_if_oidc
def get_deleted_zeppelin_instances():
    response = airfield_service.get_deleted_zeppelin_instances_api()
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/deleted/instance', method="GET").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/deleted/instance/<instance_id>', methods=['DELETE'])  # delete deleted instance
@UserService.login_if_oidc
def delete_instance_from_deleted_instances(instance_id):
    instance_id = clean_input_string(instance_id)
    response = AuthService.check_for_authorisation(instance_id)  # automatically checks if oidc is activated
    if response.status == ApiResponseStatus.SUCCESS:
        response = airfield_service.delete_deleted_zeppelin_instance(instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/deleted/instance/', method="DELETE").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance', methods=['POST'])  # create
@UserService.login_if_oidc
def create_zeppelin_instance():
    logging.debug('request data: {}'.format(request.data))
    instance_configuration = request.data
    response = airfield_service.create_or_update_zeppelin_instance(instance_configuration, deployment=True)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/', method="GET").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/<instance_id>', methods=['DELETE'])  # delete
@UserService.login_if_oidc
def delete_instance(instance_id):
    instance_id = clean_input_string(instance_id)
    response = AuthService.check_for_authorisation(instance_id)  # automatically checks if oidc is activated
    if response.status == ApiResponseStatus.SUCCESS:
        response = airfield_service.delete_existing_zeppelin_instance(instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/', method="DELETE").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/<instance_id>', methods=['PUT'])  # redeploy
@UserService.login_if_oidc
def redeploy_instance(instance_id):
    response = AuthService.check_for_authorisation(clean_input_string(instance_id))  # automatically checks if oidc is activated
    if response.status == ApiResponseStatus.SUCCESS:
        response = airfield_service.create_or_update_zeppelin_instance(request.data, instance_id, deployment=True)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/', method="PUT").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/commit/<instance_id>', methods=['PUT'])  # commit
@UserService.login_if_oidc
def commit_instance(instance_id):
    response = airfield_service.create_or_update_zeppelin_instance(request.data, instance_id, deployment=False)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/commit/', method="PUT").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/<instance_id>/action/restart', methods=['POST'])  # restart
@UserService.login_if_oidc
def restart_instance(instance_id):
    instance_id = clean_input_string(instance_id)
    response = airfield_service.restart_zeppelin_instance(instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/action/restart/', method="POST").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/<instance_id>/action/start', methods=['POST'])  # start
@UserService.login_if_oidc
def start_instance(instance_id):
    instance_id = clean_input_string(instance_id)
    response = airfield_service.start_zeppelin_instance(instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/action/start/', method="POST").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/<instance_id>/action/stop', methods=['POST'])  # stop
@UserService.login_if_oidc
def stop_instance(instance_id):
    instance_id = clean_input_string(instance_id)
    response = airfield_service.stop_zeppelin_instance(instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/action/stop/', method="POST").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/notebook', methods=['GET'])
@UserService.login_if_oidc
def get_stored_notebooks():
    response = airfield_service.get_stored_notebooks()
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/notebook', method="GET").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/<instance_id>/notebook', methods=['GET'])
@UserService.login_if_oidc
def get_instance_notebooks(instance_id):
    response = airfield_service.get_instance_notebooks(instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/notebook', method="GET").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/notebook', methods=['POST'])
@UserService.login_if_oidc
def export_notebook():
    username = UserService.get_user_name()
    response = airfield_service.export_notebook(request.data["data"], username, request.args.get('force'))
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/notebook', method="POST").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/<instance_id>/notebook/<notebook_id>', methods=['POST'])
@UserService.login_if_oidc
def import_notebook(instance_id, notebook_id):
    response = airfield_service.import_notebook(notebook_id, instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/notebook', method="POST").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/notebook/<notebook_id>', methods=['DELETE'])
@UserService.login_if_oidc
def delete_notebook(notebook_id):
    response = airfield_service.delete_notebook(notebook_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/notebook', method="DELETE").inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/metrics', methods=['GET'])
@UserService.login_if_oidc
def metrics():
    return Response(generate_latest())
