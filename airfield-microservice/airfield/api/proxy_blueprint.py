import threading
from flask import Blueprint, request, Response
from flask_sockets import Sockets
import requests
import websocket
from airfield.core import AuthService, airfield_service, UserService
from airfield.utility import ApiResponseStatus

ProxyBlueprint = Blueprint('proxy', __name__)
WebsocketBlueprint = Blueprint('websocket', __name__)
sockets = Sockets()


@WebsocketBlueprint.route('/proxy/<instance_id>/ws')
@UserService.login_if_oidc
def websocket_proxy(ws, instance_id=None):
    response = AuthService.check_for_authorisation(instance_id)  # automatically checks if oidc is activated
    if response.status != ApiResponseStatus.SUCCESS:
        return response.to_json(), response.status.value
    client = websocket.WebSocket()
    ip, port = airfield_service.get_instance_ip_address_and_port(instance_id)
    base_url = f'{ip}:{port}'
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


@ProxyBlueprint.route("/proxy/<string:instance_id>/", defaults={'path': ''})
@ProxyBlueprint.route("/proxy/<string:instance_id>/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
@UserService.login_if_oidc
def proxy(instance_id, path):
    response = AuthService.check_for_authorisation(instance_id)  # automatically checks if oidc is activated
    print(response)
    if response.status != ApiResponseStatus.SUCCESS:
        return response.to_json(), response.status.value
    ip, port = airfield_service.get_instance_ip_address_and_port(instance_id)
    base_url = f'{ip}:{port}'
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
