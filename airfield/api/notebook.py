"""API for notebook management"""

from flask import Blueprint, request
from .auth import require_login
from ..util import metrics, dependency_injection as di
from ..service.notebook import NotebookService
from . import auth
from ..util.exception import ConflictError


notebook_blueprint = Blueprint('notebook', __name__)


def register_blueprint(app):
    app.register_blueprint(notebook_blueprint)


def instrumented_route(endpoint, method):
    def wrapped(f):
        return require_login(metrics.api_endpoint(endpoint, method)(notebook_blueprint.route(endpoint, methods=[method])(f)))
    return wrapped


@instrumented_route('/api/notebook', 'GET')
def get_stored_notebooks():
    return di.get(NotebookService).get_stored_notebooks()


@instrumented_route('/api/notebook', 'POST')
def export_notebook():
    data = request.get_json()
    force = request.args.get('force', 'false').lower() == 'true'
    username = auth.get_user_name()
    instance_id = data["instance_id"]
    notebook_id = data["notebook_id"]
    status = 200
    msg = ''
    try:
        notebook_id = di.get(NotebookService).export_notebook(instance_id, notebook_id, username, force)
    except ConflictError as e:
        status = 409
        msg = e.error
    return dict(notebook_id=notebook_id, msg=msg), status


@instrumented_route('/api/instance/<instance_id>/notebook', 'GET')
def get_instance_notebooks(instance_id):
    return di.get(NotebookService).get_instance_notebooks(instance_id)


@instrumented_route('/api/instance/<instance_id>/notebook/backup', 'POST')
def backup_notebooks(instance_id):
    di.get(NotebookService).backup_notebooks(instance_id)
    return dict(instance_id=instance_id, status="finished"), 200


@instrumented_route('/api/instance/<instance_id>/notebook/restore', 'POST')
def restore_notebooks(instance_id):
    di.get(NotebookService).restore_notebooks(instance_id)
    return dict(instance_id=instance_id, status="started"), 200


@instrumented_route('/api/instance/<instance_id>/notebook/restore', 'DELETE')
def cancel_restore_notebooks(instance_id):
    di.get(NotebookService).cancel_restore_notebooks(instance_id)
    return dict(instance_id=instance_id, status="canceled"), 200


@instrumented_route('/api/notebook/<notebook_id>/import', 'POST')
def import_notebook(notebook_id):
    data = request.get_json()
    instance_id = data["instance_id"]
    di.get(NotebookService).import_notebook(instance_id, notebook_id)
    return dict(instance_id=instance_id, notebook_id=notebook_id, status="imported"), 200


@instrumented_route('/api/notebook/<notebook_id>', 'DELETE')
def delete_notebook(notebook_id):
    di.get(NotebookService).delete_stored_notebook(notebook_id)
    return dict(notebook_id=notebook_id, status="deleted"), 200