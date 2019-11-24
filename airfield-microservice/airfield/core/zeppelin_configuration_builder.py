# -*- coding: utf-8 -*-
"""Helper class to combine standard and custom settings for Zeppelin instance configurations
and consul instance entries"""

#  standard imports
import logging
import secrets
import time
import random
import string
from enum import Enum

from jinja2 import Template
import hashlib
# custom imports
import config
from . import UserService

CREATE_NOTEBOOK_API_URL = "/api/notebook"
CONFIG_KEY = 'configuration'
ID_KEY = 'id'
LABEL_KEY = 'labels'
HOST_KEY = 'HAPROXY_0_VHOST'
COMMENT_KEY = 'comment'
LIBRARIES_KEY = 'libraries'
ZEPPELIN_SHIRO_CONFIG_KEY = 'ZEPPELIN_SHIRO_CONF'
ENV_KEY = 'env'
CPUS_KEY = "cpus"
MEM_KEY = "mem"
CREATED_AT_KEY = "created_at"
HISTORY_KEY = "history"
COMMENT_ONLY_KEY = "comment_only"
CREATED_BY_KEY = "createdBy"
DELETE_AT_KEY = "deleteAt"
USERS_KEY = "users"
INSTANCES_KEY = "instances"
USER_MANAGEMENT_KEY = "usermanagement"
COSTS_OBJECT_KEY = "costsAsObject"
URL_KEY = "url"
TEMPLATE_ID_KEY = "template_id"
PYTHON_PACKAGES_KEY = 'PYTHON_PACKAGES'
R_PACKAGES_KEY = 'R_PACKAGES'

STATUS_KEY = "status"
TIME_KEY = "time"
RESOURCES_KEY = "resources"
ZEPPELIN_KEY = "zeppelin"
SPARK_KEY = "spark"
SPARK_CORES_KEY = "SPARK_CORES_MAX"
SPARK_MEM_KEY = "SPARK_EXECUTOR_MEMORY"

INSTANCE_URL_PREFIX = 'https://'
LANGUAGE_KEY = 'language'
LANGUAGE_PYTHON = 'Python'
LANGUAGE_R = 'R'
TENSORFLOW = "tensorflow"


class InstanceRunningTypes(Enum):
    RUNNING = 0
    STOPPED = 1


class ZeppelinConfigurationBuilder(object):

    def __init__(self):
        logging.info('Initializing ConfigurationBuilder.')

    def create_instance_configuration(self, custom_configuration: dict, app_definition: dict, deployment=False):
        """
        Creates a valid Zeppelin instance configuration based on parameters specified in frontend.

        :param deployment:  only needed if the instance is redeployed
        :param custom_configuration: the settings that are customizable in the frontend
        :param app_definition: The marathon app definition for the zeppelin instance
        :return: app definition for zeppelin instance and instance metadata for consul/etcd
        """
        try:
            instance_id = custom_configuration[ID_KEY]
        except KeyError:
            instance_id = self._generate_instance_id()
        app_id = instance_id
        if config.MARATHON_APP_GROUP:
            app_id = "%s/%s" % (config.MARATHON_APP_GROUP, instance_id)
        instance_url = self.parse_url(instance_id)
        options = custom_configuration[CONFIG_KEY]
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
        app_definition[ENV_KEY][ZEPPELIN_SHIRO_CONFIG_KEY] = self._create_user_config_file(
            options[USERS_KEY],
            options[USER_MANAGEMENT_KEY]) if options[USER_MANAGEMENT_KEY] != "no" else ""

        if CREATED_AT_KEY not in custom_configuration:
            custom_configuration[CREATED_AT_KEY] = time.time()

        if CREATED_BY_KEY not in custom_configuration or custom_configuration[CREATED_BY_KEY] == '':
            custom_configuration[CREATED_BY_KEY] = UserService.get_user_name()

        # check for some options and add them if necessary
        if deployment:
            if HISTORY_KEY not in custom_configuration:  # creates history
                custom_configuration[HISTORY_KEY] = self.create_history_list(
                    [InstanceRunningTypes.STOPPED, InstanceRunningTypes.RUNNING],
                    custom_configuration)
            else:
                # adds the deployment/redeployment history
                custom_configuration[HISTORY_KEY].extend(
                    self.create_history_list(
                        [InstanceRunningTypes.STOPPED, InstanceRunningTypes.RUNNING],
                        custom_configuration))

        # overwrites the costs send from the frontend
        options[COSTS_OBJECT_KEY] = config.MEMORY_AND_CORE_COSTS

        # Create entry for config store with only selected values
        metadata = {COMMENT_KEY: custom_configuration[COMMENT_KEY],
                    CREATED_BY_KEY: custom_configuration[CREATED_BY_KEY],
                    DELETE_AT_KEY: custom_configuration[DELETE_AT_KEY],
                    CONFIG_KEY: {key: options[key] for key in
                                 # this will copy most of the values of the CONFIG_KEY entry
                                 [CPUS_KEY, ENV_KEY, MEM_KEY, INSTANCES_KEY, USERS_KEY, USER_MANAGEMENT_KEY,
                                  COSTS_OBJECT_KEY]},
                    URL_KEY: INSTANCE_URL_PREFIX + instance_url,
                    CREATED_AT_KEY: custom_configuration[CREATED_AT_KEY],
                    HISTORY_KEY: custom_configuration[HISTORY_KEY],
                    ID_KEY: instance_id,
                    TEMPLATE_ID_KEY: custom_configuration[TEMPLATE_ID_KEY]}
        # print(metadata)
        metadata[CONFIG_KEY][USERS_KEY] = [] if options[USER_MANAGEMENT_KEY] == "no" else metadata[CONFIG_KEY][
            USERS_KEY]  # remove users if no usermanagement
        metadata[CONFIG_KEY][LIBRARIES_KEY] = []
        for lib in custom_configuration[CONFIG_KEY][LIBRARIES_KEY]:  # libraries goes another level deeper
            try:
                metadata[CONFIG_KEY][LIBRARIES_KEY].append(
                    {key: lib[key] for key in {LANGUAGE_KEY, LIBRARIES_KEY, TENSORFLOW}})
            except KeyError:
                metadata[CONFIG_KEY][LIBRARIES_KEY].append({key: lib[key] for key in {LANGUAGE_KEY, LIBRARIES_KEY}})

        return app_definition, metadata

    @staticmethod
    def create_history_list(status_list, configuration):
        if isinstance(status_list, list):
            liste = []
            for status in status_list:
                liste.append(ZeppelinConfigurationBuilder.create_history_object(status, configuration))
            return liste
        else:
            return [ZeppelinConfigurationBuilder.create_history_object(status_list, configuration)]

    @staticmethod
    def create_history_object(status, configuration):
        if status in InstanceRunningTypes:
            status = status.name
        return {
            STATUS_KEY: status,
            TIME_KEY: time.time(),
            RESOURCES_KEY: {
                ZEPPELIN_KEY: {
                    CPUS_KEY: configuration[CONFIG_KEY][CPUS_KEY],
                    MEM_KEY: configuration[CONFIG_KEY][MEM_KEY]
                },
                SPARK_KEY: {
                    CPUS_KEY: configuration[CONFIG_KEY][ENV_KEY][SPARK_CORES_KEY],
                    MEM_KEY: configuration[CONFIG_KEY][ENV_KEY][SPARK_MEM_KEY]
                }
            }
        }

    def _parse_additional_packages(self, configuration: dict):
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

    @staticmethod
    def _create_python_packages_string(python_packages: list):
        """
        Builds the specific string required by Zeppelin images to install Python packages.

        :param python_packages: list containing Python package strings
        :return: the properly formatted Python packages string
        """
        if len(python_packages) is 0:
            return None
        else:
            return " ".join(python_packages)

    @staticmethod
    def _create_r_packages_string(r_packages: list):
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

    @staticmethod
    def _create_user_config_file(users: list, usermanagement: str):
        hashed_users = []
        for user in users:
            if (usermanagement == "manual" and (user["username"] == "" or user["password"] == "")) or (
                    usermanagement in ["random", "oidc"] and user["username"] == ""):
                # filter empty lines/users
                users.remove(user)
                continue
            if usermanagement == "random":
                user["password"] = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))
                # this password will be accessible outside the function because dict is a mutable type
            # hash passwords and store for template
            hashed_password = hashlib.sha256(user["password"].encode("utf-8")).hexdigest()
            hashed_users.append({"username": user["username"], "password": hashed_password})
        if len(users) is 0 or usermanagement == "oidc":
            # dont create a file if no users are to be created or oidc is choosen
            return ""
        else:
            with open("airfield/resources/shiro.ini.jinja2") as file_:
                template = Template(file_.read())
            out = template.render(users=hashed_users)
            return out

    def _generate_instance_id(self) -> str:
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(9))

    @staticmethod
    def parse_url(instance_id: str) -> str:
        url = instance_id + config.BASE_HOST
        return url
