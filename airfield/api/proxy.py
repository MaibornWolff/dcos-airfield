import threading
from flask import Blueprint, request, Response
from flask_sockets import Sockets
import requests
import websocket
from .auth import require_login, get_user_name
from ..service.instance import InstanceService
from ..util import dependency_injection as di
from ..util.serialization import clean_input_string
from ..settings import config


proxy_blueprint = Blueprint('proxy', __name__)
websocket_blueprint = Blueprint('websocket', __name__)
sockets = Sockets()
instance_service = di.get(InstanceService)


def register_blueprint(app):
    sockets.init_app(app)
    sockets.register_blueprint(websocket_blueprint)
    app.register_blueprint(proxy_blueprint)


@websocket_blueprint.route('/proxy/<instance_id>/ws')
@require_login
def websocket_proxy(ws, instance_id=None):
    instance_id = clean_input_string(instance_id)
    if config.OIDC_ACTIVATED:
        user_name = get_user_name()
        admins = instance_service.get_instance_admins(instance_id)
        if admins and user_name not in admins:
            return dict(msg="User not authorized for instance"), 403
    client = websocket.WebSocket()
    base_url = instance_service.get_instance_url(instance_id)
    client.connect(f"ws://{base_url}/ws")
    stop_event = threading.Event()

    def loop():
        while not stop_event.is_set():
            msg = client.recv()
            if msg:
                ws.send(msg)

    thread = threading.Thread(target=loop)
    thread.start()
    while not ws.closed:
        message = ws.receive()
        if message:
            client.send(message)
    stop_event.set()
    thread.join()


@proxy_blueprint.route("/proxy/<string:instance_id>/", defaults={'path': ''})
@proxy_blueprint.route("/proxy/<string:instance_id>/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
@require_login
def proxy(instance_id, path):
    instance_id = clean_input_string(instance_id)
    if config.OIDC_ACTIVATED:
        user_name = get_user_name()
        admins = instance_service.get_instance_admins(instance_id)
        if admins and user_name not in admins:
            return dict(msg="User not authorized for instance"), 403
    base_url = instance_service.get_instance_url(instance_id)
    url = f"http://{base_url}" + "/" + path
    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for (key, value) in request.headers if
                 key != 'Host' and key != "Content-Length" and key != "If-Modified-Since"},
        data=request.get_data(),
        allow_redirects=False,
        verify=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection', "Location"]
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    response = Response(resp.content, resp.status_code, headers)
    return response
