# -*- coding: utf-8 -*-
"""Helper class to combine standard and custom settings for Zeppelin instance configurations
and consul instance entries"""

#  standard imports
import logging
from datetime import datetime
# third party imports
import exrex
from deepmerge import Merger
# custom imports
import config
from airfield.core.model import DefaultConfiguration, ZeppelinInstanceMetadata


CREATE_NOTEBOOK_API_URL = "/api/notebook"
CONFIGURATION_KEY = 'configuration'
CONFIGURATION_ID_KEY = 'id'
CONFIGURATION_LABEL_KEY = 'labels'
CONFIGURATION_HOST_KEY = 'HAPROXY_0_VHOST'
CONFIGURATION_COMMENT_KEY = 'comment'
CONFIGURATION_LIBRARIES_KEY = 'libraries'
CONFIGURATION_ENV_KEY = 'env'
CONFIGURATION_PYTHON_PACKAGES_KEY = 'PYTHON_PACKAGES'
CONFIGURATION_R_PACKAGES_KEY = 'R_PACKAGES'
CONSUL_ENTRY_DELETE_AT_KEY = 'delete_at'
INSTANCE_URL_PREFIX = 'https://'
LANGUAGE_KEY = 'language'
LANGUAGE_PYTHON = 'Python'
LANGUAGE_R = 'R'


class ZeppelinConfigurationBuilder(object):

    def __init__(self):
        logging.info('Initializing ConfigurationBuilder.')

    def create_instance_configuration(self, custom_settings: dict, base_configuration: dict) -> dict:
        """
        Creates a valid Zeppelin instance configuration with parameters specified in frontend.

        :param custom_settings: the settings that are customizable in the frontend
        :param base_configuration: The basic zeppelin configuration as defined locally or on consul
        :return: a dictionary containing the valid Zeppelin instance configuration
        """
        try:
            custom_configuration = self._parse_custom_settings(custom_settings)
        except KeyError as e:
            raise e
        base_configuration[CONFIGURATION_ID_KEY] = self._generate_random_id()
        base_configuration[CONFIGURATION_LABEL_KEY][CONFIGURATION_HOST_KEY] = self._parse_url(base_configuration[CONFIGURATION_ID_KEY])
        merger = Merger([
                (list, ["append"]),
                (dict, ["merge"])
            ],
            ["override"],
            ["override"]
        )
        logging.debug('Merging instance base configuration with custom settings.')
        configuration = merger.merge(base_configuration, custom_configuration[CONFIGURATION_KEY])
        configuration = self._parse_additional_packages(configuration)
        logging.debug('Loading instance configuration dictionary into schema.')
        return configuration

    def parse_consul_instance_entry(self, input_data: dict, instance_configuration: dict) -> dict:
        """
        Parses the created instance data into a consul instance entry.

        :param input_data: some data passed from the frontend, such as comments
        :param instance_configuration: the created instance configuration
        :return: a dictionary containing the consul entry
        """
        instance_data = ZeppelinInstanceMetadata()
        instance_data.url = INSTANCE_URL_PREFIX + self._parse_url(instance_configuration[CONFIGURATION_ID_KEY])
        instance_data.id = instance_configuration[CONFIGURATION_ID_KEY]
        instance_data.comment = input_data.get(CONFIGURATION_COMMENT_KEY, None)
        instance_data.created_at = datetime.utcnow().timestamp()
        instance_data.delete_at = input_data.get(CONSUL_ENTRY_DELETE_AT_KEY, None)
        return instance_data.dump(instance_data)

    def _parse_additional_packages(self, configuration: dict) -> dict:
        """
        Airfield allows for additional R/Python packages to be defined.
        These are passed into the required format for installation here.

        :param configuration: dictionary containing the configuration
        :return: the configuration with added packages
        """
        for libraries in configuration[CONFIGURATION_LIBRARIES_KEY]:
            if libraries[LANGUAGE_KEY] == LANGUAGE_PYTHON:
                if len(libraries[CONFIGURATION_LIBRARIES_KEY]) is 0:
                    configuration[CONFIGURATION_ENV_KEY].pop(CONFIGURATION_PYTHON_PACKAGES_KEY, None)
                else:
                    python_packages = []
                    for package in libraries[CONFIGURATION_LIBRARIES_KEY]:
                        python_packages.append(package)
                    configuration[CONFIGURATION_ENV_KEY][CONFIGURATION_PYTHON_PACKAGES_KEY] = \
                        self._create_python_packages_string(python_packages)
            if libraries[LANGUAGE_KEY] == LANGUAGE_R:
                if len(libraries[CONFIGURATION_LIBRARIES_KEY]) is 0:
                    configuration[CONFIGURATION_ENV_KEY].pop(CONFIGURATION_R_PACKAGES_KEY, None)
                else:
                    r_packages = []
                    for package in libraries[CONFIGURATION_LIBRARIES_KEY]:
                        r_packages.append(package)
                    configuration[CONFIGURATION_ENV_KEY][CONFIGURATION_R_PACKAGES_KEY] = \
                        self._create_r_packages_string(r_packages)
        return configuration

    def _create_python_packages_string(self, python_packages: list):
        """
        Builds the specific string required by Zeppelin images to install Python packages.

        :param python_packages: list containing Python package strings
        :return: the properly formatted Python packages string
        """
        print("python packs:" + python_packages)
        if len(python_packages) is 0:
            return None
        else:
            tmp = python_packages
            python_packages = ""
            for package in tmp:
                python_packages += "{} ".format(package)
            return python_packages[:-1]

    def _create_r_packages_string(self, r_packages: list):
        """
        Builds the specific string required by Zeppelin images to install R packages.

        :param r_packages: list containing R package strings
        :return: the properly formatted R packages string
        """
        if len(r_packages) is 0:
            return None
        else:
            tmp = r_packages
            r_packages = "c("
            for package in tmp:
                r_packages += "'{}',".format(package)
            return r_packages[:-1] + ")"

    def _generate_random_id(self) -> str:
        random_id = exrex.getone("[a-z0-9]{9}")
        logging.debug('Generated random id for instance. id={}'.format(random_id))
        return random_id

    def _parse_url(self, instance_id: str) -> str:
        url = instance_id + config.BASE_HOST
        logging.debug('Parsed url for id. url={}'.format(url))
        return url

    def _parse_custom_settings(self, custom_settings: dict) -> dict:
        try:
            input_schema = DefaultConfiguration()
            return input_schema.load(custom_settings)
        except KeyError:
            error_message = "Failed to parse custom settings."
            raise KeyError(error_message)
