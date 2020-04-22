import threading

import requests
import websocket
from flask import Blueprint, request, Response
from flask_sockets import Sockets

from .auth import require_login, get_user_name
from ..service.instance import InstanceService
from ..settings import config
from ..util import dependency_injection as di
from ..util.serialization import clean_input_string

proxy_blueprint = Blueprint("proxy", __name__)
websocket_blueprint = Blueprint("websocket", __name__)
sockets = Sockets()
instance_service = di.get(InstanceService)


def register_blueprint(app):
    sockets.init_app(app)
    sockets.register_blueprint(websocket_blueprint)
    app.register_blueprint(proxy_blueprint)


def websocket_proxy_body(ws, instance_id=None, header=None, kernel_id=None):
    client = websocket.WebSocket()
    base_url = instance_service.get_instance_url(instance_id)
    if kernel_id is not None:
        url = "ws://{}/proxy/{}/api/kernels/{}/channels?{}".format(base_url, instance_id, kernel_id,
                                                                   request.query_string.decode("utf-8"))
    else:
        url = "ws://{}/ws".format(base_url)

    if header is None:
        client.connect(url)
    else:
        client.connect(url,
                       header=header)
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


@websocket_blueprint.route("/proxy/<instance_id>/ws")
@require_login
def websocket_proxy_zeppelin(ws, instance_id=None):
    instance_id = clean_input_string(instance_id)
    if config.OIDC_ACTIVATED:
        user_name = get_user_name()
        admins = instance_service.get_instance_admins(instance_id)
        if admins and user_name not in admins:
            return dict(msg="User not authorized for instance"), 403
    websocket_proxy_body(ws=ws, instance_id=instance_id)


@websocket_blueprint.route("/proxy/<string:instance_id>/api/kernels/<string:kernel_id>/channels")
@require_login
def websocket_proxy_jupyter(ws, instance_id=None, kernel_id=None):
    instance_id = clean_input_string(instance_id)
    if config.OIDC_ACTIVATED:
        user_name = get_user_name()
        admins = instance_service.get_instance_admins(instance_id)
        if admins and user_name not in admins:
            return dict(msg="User not authorized for instance"), 403
    websocket_proxy_body(ws=ws, instance_id=instance_id, kernel_id=kernel_id, header={key: value for (key, value) in request.headers if key != "Host" and key != "Content-Length" and key != "If-Modified-Since"})


@proxy_blueprint.route("/proxy/<string:instance_id>/", defaults={"path": ""})
@proxy_blueprint.route("/proxy/<string:instance_id>/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
@require_login
def proxy(instance_id, path):
    instance_id = clean_input_string(instance_id)
    if config.OIDC_ACTIVATED:
        user_name = get_user_name()
        admins = instance_service.get_instance_admins(instance_id)
        if admins and user_name not in admins:
            return dict(msg="User not authorized for instance"), 403
    instance_type = instance_service.get_instance_type(instance_id)
    base_url = instance_service.get_instance_url(instance_id)
    if instance_type == "jupyter":
        base_url = "{}/proxy/{}".format(base_url, instance_id)
    url = "http://{}/{}".format(base_url, path)
    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for (key, value) in request.headers if
                 key != "Host" and key != "Content-Length" and key != "If-Modified-Since"},
        data=request.get_data(),
        allow_redirects=False,
        verify=False)
    excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
    if instance_type == "zeppelin":
        excluded_headers.append("location")
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    response = Response(resp.content, resp.status_code, headers)
    return response
