# -*- coding: utf-8 -*-
"""Helper class to combine standard and custom settings for Zeppelin instance configurations
and consul instance entries"""

#  standard imports
import logging
from datetime import datetime
import random
import string
# custom imports
import config


CREATE_NOTEBOOK_API_URL = "/api/notebook"
KEY = 'configuration'
ID_KEY = 'id'
LABEL_KEY = 'labels'
HOST_KEY = 'HAPROXY_0_VHOST'
COMMENT_KEY = 'comment'
LIBRARIES_KEY = 'libraries'
ENV_KEY = 'env'
CPUS_KEY = "cpus"
MEM_KEY = "mem"
PYTHON_PACKAGES_KEY = 'PYTHON_PACKAGES'
R_PACKAGES_KEY = 'R_PACKAGES'
DELETE_AT_KEY = 'delete_at'
INSTANCE_URL_PREFIX = 'https://'
LANGUAGE_KEY = 'language'
LANGUAGE_PYTHON = 'Python'
LANGUAGE_R = 'R'
TENSORFLOW = "tensorflow"


class ZeppelinConfigurationBuilder(object):

    def __init__(self):
        logging.info('Initializing ConfigurationBuilder.')

    def create_instance_configuration(self, custom_configuration: dict, app_definition: dict):
        """
        Creates a valid Zeppelin instance configuration based on parameters specified in frontend.

        :param custom_configuration: the settings that are customizable in the frontend
        :param app_definition: The marathon app definition for the zeppelin instance
        :return: app definition for zeppelin instance and instance metadata for consul/etcd
        """
        instance_id = self._generate_instance_id()
        app_id = instance_id
        if config.MARATHON_APP_GROUP:
            app_id = "%s/%s" % (config.MARATHON_APP_GROUP, instance_id)
        instance_url = self._parse_url(instance_id)
        options = custom_configuration[KEY]
        # Add configuration options to app definition
        app_definition[ID_KEY] = app_id
        app_definition[LABEL_KEY][HOST_KEY] = instance_url
        app_definition[CPUS_KEY] = int(options[CPUS_KEY])
        app_definition[MEM_KEY] = int(options[MEM_KEY])
        for key, value in options[ENV_KEY].items():
            app_definition[ENV_KEY][key] = value
        python_packages_string, r_packages_string = self._parse_additional_packages(options)
        if python_packages_string:
            app_definition[ENV_KEY][PYTHON_PACKAGES_KEY] = python_packages_string
        if r_packages_string:
            app_definition[ENV_KEY][R_PACKAGES_KEY] = r_packages_string
        # Create config entry for config store
        metadata = dict(
            url=INSTANCE_URL_PREFIX + instance_url,
            id=instance_id,
            comment=custom_configuration.get(COMMENT_KEY, None),
            created_at=datetime.utcnow().timestamp(),
            delete_at=custom_configuration.get(DELETE_AT_KEY, None)
        )
        return app_definition, metadata

    def _parse_additional_packages(self, configuration: dict) -> dict:
        """
        Airfield allows for additional R/Python packages to be defined.
        These are passed into the required format for installation here.

        :param configuration: dictionary containing the configuration
        :return: the configuration with added packages
        """
        python_packages_string = None
        r_packages_string = None
        for libraries in configuration[LIBRARIES_KEY]:
            if libraries[LANGUAGE_KEY] == LANGUAGE_PYTHON:
                if len(libraries[LIBRARIES_KEY]) > 0:
                    python_packages = []
                    for package in libraries[LIBRARIES_KEY]:
                        python_packages.append(package)
                    if libraries.get(TENSORFLOW, False):
                        python_packages.append(TENSORFLOW)
                    python_packages_string = self._create_python_packages_string(python_packages)
            if libraries[LANGUAGE_KEY] == LANGUAGE_R:
                if len(libraries[LIBRARIES_KEY]) > 0:
                    r_packages = []
                    for package in libraries[LIBRARIES_KEY]:
                        r_packages.append(package)
                    r_packages_string = self._create_r_packages_string(r_packages)
        return python_packages_string, r_packages_string

    def _create_python_packages_string(self, python_packages: list):
        """
        Builds the specific string required by Zeppelin images to install Python packages.

        :param python_packages: list containing Python package strings
        :return: the properly formatted Python packages string
        """
        if len(python_packages) is 0:
            return None
        else:
            return " ".join(python_packages)

    def _create_r_packages_string(self, r_packages: list):
        """
        Builds the specific string required by Zeppelin images to install R packages.

        :param r_packages: list containing R package strings
        :return: the properly formatted R packages string
        """
        if len(r_packages) is 0:
            return None
        else:
            package_string = ','.join(["'%s'" % p for p in r_packages])
            return "c(%s)" % package_string

    def _generate_instance_id(self) -> str:
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(9))

    def _parse_url(self, instance_id: str) -> str:
        url = instance_id + config.BASE_HOST
        return url
