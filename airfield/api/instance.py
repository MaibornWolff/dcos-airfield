"""API for instance management"""

import json

from flask import Blueprint, request

from .auth import require_login, get_user_name
from ..service.instance import InstanceService
from ..service.notebook import NotebookService
from ..settings import config
from ..util import metrics, dependency_injection as di
from ..util.exception import ConfigurationException, HostNetworkException
from ..util.logging import logger
from ..util.serialization import clean_input_string

instance_blueprint = Blueprint('instance', __name__)


def register_blueprint(app):
    app.register_blueprint(instance_blueprint)


def instrumented_route(endpoint, method):
    def wrapped(f):
        return metrics.api_endpoint(endpoint, method)(
            instance_blueprint.route(endpoint, endpoint="{}-{}".format(endpoint, method), methods=[method])(
                require_login(f)))
    return wrapped


def instance_admin_required(func):
    def wrapper(instance_id, *args):
        instance_id = clean_input_string(instance_id)
        if config.OIDC_ACTIVATED:
            user_name = get_user_name()
            admins = di.get(InstanceService).get_instance_admins(instance_id)
            if admins and user_name not in admins:
                return dict(msg="User not authorized for instance."), 403
        return func(instance_id, *args)

    return wrapper


@instrumented_route('/api/instance_prices', 'GET')
def get_prices():
    """
    Returns the costs for a single core of an instance and for a single GB RAM for an instance.
    """
    return {
        'cost_tracking_enabled': config.COST_TRACKING_ENABLED,
        'cost_currency': config.COST_CURRENCY,
        'cost_core_per_minute': config.COST_CORE_PER_MINUTE,
        'cost_gb_per_minute': config.COST_GB_PER_MINUTE
    }


@instrumented_route('/api/instance_costs', 'GET')
def calculate_costs():
    """Returns the costs per hour for an instance configuration"""
    data = json.loads(request.args.get("configuration"))
    return di.get(InstanceService).calculate_costs_per_hour(data)


@instrumented_route('/api/instance_configurations', 'GET')
def get_default_configurations():
    """Returns a list of available instance configurations"""
    return di.get(InstanceService).get_default_configurations()


@instrumented_route('/api/instance', 'GET')
def get_instances():
    """Returns a list of all instances"""
    show_deleted = request.args.get("deleted", "false").lower() == "true"
    return di.get(InstanceService).get_instances(deleted=show_deleted)


@instrumented_route('/api/instance/<instance_id>/details', 'GET')
def get_instance(instance_id):
    """Returns the details of a single instance"""
    show_deleted = request.args.get("deleted", "false").lower() == "true"
    return di.get(InstanceService).get_instance(instance_id=instance_id, deleted=show_deleted)


@instrumented_route('/api/instance', 'POST')
def create_instance():
    data = request.get_json()
    logger.debug('request data: {}'.format(data))
    username = get_user_name()
    instance_configuration = data["configuration"]
    notebook_template = data.get("notebook_template")
    try:
        instance_id = di.get(InstanceService).create_instance(instance_configuration, username)
        if notebook_template:
            di.get(NotebookService).import_notebook_template(instance_id, notebook_template)
        return dict(instance_id=instance_id), 200
    except ConfigurationException as e:
        return dict(msg=e.error), 409
    except HostNetworkException as e:
        return dict(msg=e.error), 501



@instrumented_route('/api/instance/<instance_id>/state', 'GET')
def get_instance_state(instance_id):
    return di.get(InstanceService).get_instance_state(instance_id)


@instrumented_route('/api/instance/<instance_id>/configuration', 'GET')
def get_instance_configuration(instance_id):
    return di.get(InstanceService).get_instance_configuration(instance_id)


@instrumented_route('/api/instance/<instance_id>/credentials', 'GET')
def get_instance_credentials(instance_id):
    return di.get(InstanceService).get_instance_credentials(instance_id)


@instrumented_route('/api/instance/<instance_id>', 'DELETE')
@instance_admin_required
def delete_instance(instance_id):
    di.get(InstanceService).delete_instance(instance_id)
    return dict(instance_id=instance_id, status="deleted"), 200


@instrumented_route('/api/instance/<instance_id>', 'PUT')
@instance_admin_required
def update_instance(instance_id):
    """Updates the configuration for an instance. If needed a redeploy of the instance is triggered"""
    di.get(InstanceService).update_instance(instance_id, request.data["configuration"])
    return dict(instance_id=instance_id, status="updated"), 200


@instrumented_route('/api/instance/<instance_id>/restart', 'POST')
@instance_admin_required
def restart_instance(instance_id):
    status = di.get(InstanceService).restart_instance(instance_id)
    return dict(instance_id=instance_id, status=status), 200


@instrumented_route('/api/instance/<instance_id>/start', 'POST')
@instance_admin_required
def start_instance(instance_id):
    status = di.get(InstanceService).start_instance(instance_id)
    return dict(instance_id=instance_id, status=status), 200


@instrumented_route('/api/instance/<instance_id>/stop', 'POST')
@instance_admin_required
def stop_instance(instance_id):
    status = di.get(InstanceService).stop_instance(instance_id)
    return dict(instance_id=instance_id, status=status), 200
