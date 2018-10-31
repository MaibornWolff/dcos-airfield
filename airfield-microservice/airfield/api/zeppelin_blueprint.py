# -*- coding: utf-8 -*-
"""API routes for zeppelin interactions."""

#  standard imports
import logging
# third party imports
from flask import Blueprint, request, Response
from prometheus_client import generate_latest, Counter
# custom imports
from airfield.core import AirfieldService
from airfield.utility.serialization_utilities import clean_input_string
import config
from app import oidc


ZeppelinBlueprint = Blueprint('zeppelin', __name__)
airfield_service = AirfieldService()


airfield_requests_metrics = Counter('airfield_requests_total', 'HTTP Requests', ['endpoint'])


@ZeppelinBlueprint.route('/instance/state/<instance_id>', methods=['GET'])
@oidc.accept_token(require_token=config.OIDC_ACTIVATED)
def get_zeppelin_server_state(instance_id):
    instance_id = clean_input_string(instance_id)
    response = airfield_service.get_zeppelin_instance_status(instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/state/').inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/configurations', methods=['GET'])
@oidc.accept_token(require_token=config.OIDC_ACTIVATED)
def get_zeppelin_default_configurations():
    response = airfield_service.get_zeppelin_default_configurations()
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/configurations/').inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/retrieve/all', methods=['GET'])
@oidc.accept_token(require_token=config.OIDC_ACTIVATED)
def get_zeppelin_instances():
    response = airfield_service.get_existing_zeppelin_instances()
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/retrieve/all').inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/create', methods=['POST'])
@oidc.accept_token(require_token=config.OIDC_ACTIVATED)
def create_zeppelin_instance():
    logging.debug('request data: {}'.format(request.data))
    instance_configuration = request.data
    response = airfield_service.create_zeppelin_instance(instance_configuration)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/create/').inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/delete/<instance_id>', methods=['PUT'])
@oidc.accept_token(require_token=config.OIDC_ACTIVATED)
def delete_instance(instance_id):
    instance_id = clean_input_string(instance_id)
    response = airfield_service.delete_zeppelin_instance(instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/delete/').inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/restart/<instance_id>', methods=['PUT'])
@oidc.accept_token(require_token=config.OIDC_ACTIVATED)
def restart_instance(instance_id):
    instance_id = clean_input_string(instance_id)
    response = airfield_service.restart_zeppelin_instance(instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/restart/').inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/start/<instance_id>', methods=['PUT'])
@oidc.accept_token(require_token=config.OIDC_ACTIVATED)
def start_instance(instance_id):
    instance_id = clean_input_string(instance_id)
    response = airfield_service.start_zeppelin_instance(instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/start/').inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/instance/stop/<instance_id>', methods=['PUT'])
@oidc.accept_token(require_token=config.OIDC_ACTIVATED)
def stop_instance(instance_id):
    instance_id = clean_input_string(instance_id)
    response = airfield_service.stop_zeppelin_instance(instance_id)
    airfield_requests_metrics.labels(endpoint='/api/zeppelin/instance/stop/').inc()
    return response.to_json(), response.status.value


@ZeppelinBlueprint.route('/metrics', methods=['GET'])
@oidc.accept_token(require_token=config.OIDC_ACTIVATED)
def metrics():
    return Response(generate_latest())
