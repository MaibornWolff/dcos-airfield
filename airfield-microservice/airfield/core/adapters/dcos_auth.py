# -*- coding: utf-8 -*-
"""Provides different authentication methods for DC/OS."""

#  standard imports
import json
import os
import time
import jwt
import logging
import requests
import subprocess
from requests.auth import AuthBase
# third party imports
# custom imports
import config


DCOS_CLI_TOKEN_SUBPROCESS = ["dcos", "config", "show", "core.dcos_acs_token"]
DCOS_CLI_URL_SUBPROCESS = ["dcos", "config", "show", "core.dcos_url"]


class StaticTokenAuth(AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, auth_request):
        auth_request.headers['Authorization'] = 'token=' + self.token
        return auth_request


class UsernamePasswordAuth(AuthBase):
    def __init__(self, username, password, login_endpoint):
        self.uid = username
        self.password = password
        self.login_endpoint = login_endpoint
        self.verify = False
        self.auth_header = None
        self.expiry = 0

    def __call__(self, auth_request):
        self.refresh_auth_header()
        auth_request.headers['Authorization'] = self.auth_header
        return auth_request

    def refresh_auth_header(self):
        now = int(time.time())
        if not self.auth_header or now >= self.expiry - 10:
            self.expiry = now + 3600

            data = {
                'uid': self.uid,
                'password': self.password,
                # This is the expiry for the token itself
                'exp': self.expiry,
            }
            r = requests.post(self.login_endpoint,
                              json=data,
                              timeout=(3.05, 46),
                              verify=self.verify)
            r.raise_for_status()

            self.auth_header = 'token=' + r.cookies['dcos-acs-auth-cookie']


class DCOSAuth(AuthBase):
    def __init__(self, credentials, ca_cert):
        creds = cleanup_json(json.loads(credentials))
        self.uid = creds['uid']
        self.private_key = creds['private_key']
        self.login_endpoint = creds['login_endpoint']
        self.verify = False
        self.auth_header = None
        self.expiry = 0
        if ca_cert:
            self.verify = ca_cert

    def __call__(self, auth_request):
        self.refresh_auth_header()
        auth_request.headers['Authorization'] = self.auth_header
        return auth_request

    def refresh_auth_header(self):
        now = int(time.time())
        if not self.auth_header or now >= self.expiry - 10:
            self.expiry = now + 3600
            payload = {
                'uid': self.uid,
                # This is the expiry of the auth request params
                'exp': now + 60,
            }
            token = jwt.encode(payload, self.private_key, 'RS256')

            data = {
                'uid': self.uid,
                'token': token.decode('ascii'),
                # This is the expiry for the token itself
                'exp': self.expiry,
            }
            r = requests.post(self.login_endpoint,
                              json=data,
                              timeout=(3.05, 46),
                              verify=self.verify)
            r.raise_for_status()

            self.auth_header = 'token=' + r.cookies['dcos-acs-auth-cookie']


def cleanup_json(data):
    if isinstance(data, dict):
        return {k: cleanup_json(v) for k, v in data.items() if v is not None}
    if isinstance(data, list):
        return [cleanup_json(e) for e in data]
    return data


def get_dcos_url_from_cli():
    try:
        res = subprocess.run(DCOS_CLI_URL_SUBPROCESS, shell=False, stdout=subprocess.PIPE)
        if res.returncode == 0:
            return res.stdout.strip().decode("utf-8")
        else:
            return None
    except:
        return None


def get_dcos_token_from_cli():
    try:
        res = subprocess.run(DCOS_CLI_TOKEN_SUBPROCESS, shell=False, stdout=subprocess.PIPE)
        if res.returncode == 0:
            return res.stdout.strip().decode("utf-8")
        else:
            return None
    except Exception as ex:
        print(ex)
        return None


def retrieve_auth():
    logging.info('Retrieving DCOS authentication.')
    if config.DCOS_SERVICE_ACCOUNT_CREDENTIAL is not None:
        logging.debug('Using service account authentication.')
        return config.DCOS_BASE_URL, \
               DCOSAuth(config.DCOS_SERVICE_ACCOUNT_CREDENTIAL, None)
    elif config.DCOS_USERNAME is not None:
        logging.debug('Using user-password based authentication.')
        username = config.DCOS_USERNAME
        password = config.DCOS_PASSWORD
        login_url = config.DCOS_LOGIN_URL
        base_url = config.DCOS_BASE_URL
        return base_url, UsernamePasswordAuth(username, password, login_url)
    else:
        logging.debug('Using token-based authentication.')
        token = get_dcos_token_from_cli()
        if not token:
            raise Exception("No credentials provided")
        return get_dcos_url_from_cli(), StaticTokenAuth(token)
