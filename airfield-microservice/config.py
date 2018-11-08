# -*- coding: utf-8 -*-
"""
Contains all customizable settings in form of environment variables.

Some of the settings have default values that are used if the env variable is not set.
These are defined in this file as well.

Caution: If there is no default value for a setting, then the system will crash if that env variable
is not set. This is to ensure all important settings are configured.

The settings are grouped by topic:
1. Required settings (Application will not start, if these are not set)
2. General settings
3. OpenID Connect settings
4. Etcd adapter settings
5. DC/OS authentication settings
"""
import os


# -------------------------------------------------------------------------------
# 1. Required settings
# -------------------------------------------------------------------------------
BASE_HOST = os.environ['AIRFIELD_BASE_HOST']

# -------------------------------------------------------------------------------
# 2. General settings
# -------------------------------------------------------------------------------
APP_SECRET = 'super-secret-key'

SESSION_TYPE = 'filesystem'

STATIC_FOLDER = os.getenv('AIRFIELD_STATIC_FOLDER_PATH', './../airfield-frontend/dist/files')

TEMPLATE_FOLDER = os.getenv('AIRFIELD_TEMPLATE_FOLDER_PATH', './../airfield-frontend/dist')

API_PREFIX = os.getenv('AIRFIELD_API_PREFIX', '/api/zeppelin')

LOCAL_ZEPPELIN_DEFAULT_CONFIG_DIRECTORY = os.getenv('AIRFIELD_LOCAL_ZEPPELIN_DEFAULT_CONFIGS',
                                                    'airfield/resources/default_configurations.json')

MARATHON_APP_DEFINITION_FILE = os.getenv('AIRFIELD_MARATHON_APP_DEFINITION_FILE',
                                                 'airfield/resources/zeppelin_marathon.json')

LOGGING_LEVEL = os.getenv('AIRFIELD_LOGGING_LEVEL', 'INFO')

MARATHON_APP_GROUP = os.getenv("AIRFIELD_MARATHON_APP_GROUP", "airfield-zeppelin")

# -------------------------------------------------------------------------------
# 3. OpenID Connect settings
# -------------------------------------------------------------------------------
OIDC_CLIENT_SECRETS = os.getenv('AIRFIELD_OIDC_SECRET_FILE_PATH', 'airfield/resources/keycloak.json')

OIDC_SECRET_KEY = os.getenv('AIRFIELD_OIDC_SECRET_KEY', 'i-love-airfield')

OIDC_ACTIVATED = os.getenv('AIRFIELD_OIDC_ACTIVATED', False)

"""
    Only supports one valid issuer at this time because env variables are key-value with no array support.
    """
OIDC_VALID_ISSUER = os.getenv('AIRFIELD_OIDC_VALID_ISSUERS',
                              'http://localhost:8080/auth/realms/airfield')

OIDC_OPENID_REALM = os.getenv('AIRFIELD_OIDC_OPENID_REALM', 'airfield')

OIDC_ID_TOKEN_COOKIE_SECURE = os.getenv('AIRFIELD_OIDC_ID_TOKEN_COOKIE_SECURE', False)

OIDC_REQUIRE_VERIFIED_EMAIL = os.getenv('AIRFIELD_OIDC_REQUIRE_VERIFIED_EMAIL', False)

# -------------------------------------------------------------------------------
# 4. consul/etcd adapter settings
# -------------------------------------------------------------------------------
ETCD_ENDPOINT = os.getenv('AIRFIELD_ETCD_ENDPOINT')
CONSUL_ENDPOINT = os.getenv('AIRFIELD_CONSUL_ENDPOINT')


CONFIG_BASE_KEY = os.getenv('AIRFIELD_CONFIG_BASE_KEY', 'airfield')

# -------------------------------------------------------------------------------
# 5. DC/OS authentication settings
# -------------------------------------------------------------------------------
DCOS_SERVICE_ACCOUNT_CREDENTIAL = os.getenv('DCOS_SERVICE_ACCOUNT_CREDENTIAL', None)

DCOS_LOGIN_URL = os.getenv('DCOS_LOGIN_URL',
                           'https://leader.mesos:443/acs/api/v1/auth/login')

DCOS_BASE_URL = os.getenv('DCOS_BASE_URL', 'https://leader.mesos:443/')

DCOS_USERNAME = os.getenv('DCOS_USERNAME', None)

DCOS_PASSWORD = os.getenv('DCOS_PASSWORD', None)

WAIT_FOR_DEPLOYMENT = False
