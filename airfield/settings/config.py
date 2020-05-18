"""This module contains configuration settings that can be set on installation/startup"""

import json
import os
import base64

## Base config

LOGGING_LEVEL = os.getenv('AIRFIELD_LOGGING_LEVEL', 'INFO')

ETCD_ENDPOINT = os.getenv('AIRFIELD_ETCD_ENDPOINT')
CONSUL_ENDPOINT = os.getenv('AIRFIELD_CONSUL_ENDPOINT')
CONFIG_BASE_KEY = os.getenv('AIRFIELD_CONFIG_BASE_KEY', 'airfield')

## Zeppelin config

HDFS_CONFIG_FOLDER = os.getenv("HDFS_CONFIG_FOLDER", "").rstrip("/")
ZEPPELIN_DOCKER_IMAGE = os.getenv("ZEPPELIN_DOCKER_IMAGE")
SPARK_MESOS_EXECUTOR_DOCKER_IMAGE = os.getenv("SPARK_MESOS_EXECUTOR_DOCKER_IMAGE")

## Cost config

COST_TRACKING_ENABLED = os.getenv("AIRFIELD_COST_TRACKING_ENABLED", "false").lower() == "true"
COST_CURRENCY = os.getenv("AIRFIELD_COST_CURRENCY", "EURO")
COST_CORE_PER_MINUTE = float(os.getenv("AIRFIELD_COST_CORE_PER_MINUTE", "0.0"))
COST_GB_PER_MINUTE = float(os.getenv("AIRFIELD_COST_GB_PER_MINUTE", "0.0"))

## DC/OS config

MARATHON_APP_GROUP = os.getenv("AIRFIELD_MARATHON_APP_GROUP", "airfield-zeppelin")
DCOS_GROUPS_ENABLED = os.getenv("AIRFIELD_DCOS_GROUPS_ENABLED", "false").lower() == "true"
if os.getenv("AIRFIELD_DCOS_GROUPS_MAPPING_BASE64"):
    DCOS_GROUPS_MAPPING = json.loads(base64.b64decode(os.getenv("AIRFIELD_DCOS_GROUPS_MAPPING_BASE64")))
elif os.getenv("AIRFIELD_DCOS_GROUPS_MAPPING"):
    DCOS_GROUPS_MAPPING = json.loads(os.getenv("AIRFIELD_DCOS_GROUPS_MAPPING"))
else:
    DCOS_GROUPS_MAPPING = {}

DCOS_SERVICE_ACCOUNT_CREDENTIAL = os.getenv('DCOS_SERVICE_ACCOUNT_CREDENTIAL', None)
DCOS_LOGIN_URL = os.getenv('DCOS_LOGIN_URL', 'https://leader.mesos:443/acs/api/v1/auth/login')
DCOS_BASE_URL = os.getenv('DCOS_BASE_URL', 'https://leader.mesos:443/')
DCOS_USERNAME = os.getenv('DCOS_USERNAME', None)
DCOS_PASSWORD = os.getenv('DCOS_PASSWORD', None)

## OIDC specific config

OIDC_ACTIVATED = os.getenv('AIRFIELD_OIDC_ACTIVATED', "false").lower() == "true"
OIDC_CLIENT_SECRETS = os.path.join(os.getcwd(), "oidc_secrets.json")
OIDC_CLIENT_SECRETS_BASE64 = os.getenv('AIRFIELD_OIDC_SECRET_BASE64', None)
SECRET_KEY = os.getenv('AIRFIELD_OIDC_SECRET_KEY', 'i-love-airfield')  # this can be set at random
"""
See https://flask-oidc.readthedocs.io/en/latest/ for documentation of the following variables
"""
OIDC_VALID_ISSUER = os.getenv('AIRFIELD_OIDC_VALID_ISSUERS', 'http://localhost:8080/auth/realms/airfield')
OIDC_OPENID_REALM = os.getenv('AIRFIELD_OIDC_OPENID_REALM', 'airfield')
OIDC_ID_TOKEN_COOKIE_SECURE = os.getenv('AIRFIELD_OIDC_ID_TOKEN_COOKIE_SECURE', "false").lower() == "true"
OIDC_REQUIRE_VERIFIED_EMAIL = os.getenv('AIRFIELD_OIDC_REQUIRE_VERIFIED_EMAIL', "false").lower() == "true"