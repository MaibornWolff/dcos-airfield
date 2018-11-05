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
CONFIGURATION_KEY = 'configuration'
CONFIGURATION_ID_KEY = 'id'
CONFIGURATION_LABEL_KEY = 'labels'
CONFIGURATION_HOST_KEY = 'HAPROXY_0_VHOST'
CONFIGURATION_COMMENT_KEY = 'comment'
CONFIGURATION_LIBRARIES_KEY = 'libraries'
CONFIGURATION_ENV_KEY = 'env'
CONFIGURATION_CPUS_KEY = "cpus"
CONFIGURATION_MEM_KEY = "mem"
CONFIGURATION_PYTHON_PACKAGES_KEY = 'PYTHON_PACKAGES'
CONFIGURATION_R_PACKAGES_KEY = 'R_PACKAGES'
CONSUL_ENTRY_DELETE_AT_KEY = 'delete_at'
INSTANCE_URL_PREFIX = 'https://'
LANGUAGE_KEY = 'language'
LANGUAGE_PYTHON = 'Python'
LANGUAGE_R = 'R'
TENSORFLOW = "tensorflow"


class ZeppelinConfigurationBuilder(object):

    def __init__(self):
        logging.info('Initializing ConfigurationBuilder.')

    def create_instance_configuration(self, custom_configuration: dict, base_configuration: dict) -> dict:
        """
        Creates a valid Zeppelin instance configuration with parameters specified in frontend.

        :param custom_configuration: the settings that are customizable in the frontend
        :param base_configuration: The basic zeppelin configuration as defined locally or on consul
        :return: a dictionary containing the valid Zeppelin instance configuration
        """
        base_configuration[CONFIGURATION_ID_KEY] = self._generate_random_id()
        base_configuration[CONFIGURATION_LABEL_KEY][CONFIGURATION_HOST_KEY] = self._parse_url(base_configuration[CONFIGURATION_ID_KEY])

        configuration_options = custom_configuration[CONFIGURATION_KEY]

        base_configuration[CONFIGURATION_CPUS_KEY] = int(configuration_options[CONFIGURATION_CPUS_KEY])
        base_configuration[CONFIGURATION_MEM_KEY] = int(configuration_options[CONFIGURATION_MEM_KEY])
        for key, value in configuration_options[CONFIGURATION_ENV_KEY].items():
            base_configuration[CONFIGURATION_ENV_KEY][key] = value
        python_packages_string, r_packages_string = self._parse_additional_packages(configuration_options)
        if python_packages_string:
            base_configuration[CONFIGURATION_ENV_KEY][CONFIGURATION_PYTHON_PACKAGES_KEY] = python_packages_string
        if r_packages_string:
            base_configuration[CONFIGURATION_ENV_KEY][CONFIGURATION_R_PACKAGES_KEY] = r_packages_string
        return base_configuration

    def parse_consul_instance_entry(self, input_data: dict, instance_configuration: dict) -> dict:
        """
        Parses the created instance data into a consul instance entry.

        :param input_data: some data passed from the frontend, such as comments
        :param instance_configuration: the created instance configuration
        :return: a dictionary containing the consul entry
        """
        return dict(
            url=INSTANCE_URL_PREFIX + self._parse_url(instance_configuration[CONFIGURATION_ID_KEY]),
            id=instance_configuration[CONFIGURATION_ID_KEY],
            comment=input_data.get(CONFIGURATION_COMMENT_KEY, None),
            created_at=datetime.utcnow().timestamp(),
            delete_at=input_data.get(CONSUL_ENTRY_DELETE_AT_KEY, None)
        )

    def _parse_additional_packages(self, configuration: dict) -> dict:
        """
        Airfield allows for additional R/Python packages to be defined.
        These are passed into the required format for installation here.

        :param configuration: dictionary containing the configuration
        :return: the configuration with added packages
        """
        python_packages_string = None
        r_packages_string = None
        for libraries in configuration[CONFIGURATION_LIBRARIES_KEY]:
            if libraries[LANGUAGE_KEY] == LANGUAGE_PYTHON:
                if len(libraries[CONFIGURATION_LIBRARIES_KEY]) > 0:
                    python_packages = []
                    for package in libraries[CONFIGURATION_LIBRARIES_KEY]:
                        python_packages.append(package)
                    if libraries.get(TENSORFLOW, False):
                        python_packages.append(TENSORFLOW)
                    python_packages_string = self._create_python_packages_string(python_packages)
            if libraries[LANGUAGE_KEY] == LANGUAGE_R:
                if len(libraries[CONFIGURATION_LIBRARIES_KEY]) > 0:
                    r_packages = []
                    for package in libraries[CONFIGURATION_LIBRARIES_KEY]:
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

    def _generate_random_id(self) -> str:
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(9))

    def _parse_url(self, instance_id: str) -> str:
        url = instance_id + config.BASE_HOST
        return url
