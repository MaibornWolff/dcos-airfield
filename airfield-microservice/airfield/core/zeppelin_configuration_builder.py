# -*- coding: utf-8 -*-
"""Helper class to combine standard and custom settings for Zeppelin instance configurations
and consul instance entries"""

#  standard imports
import logging
import secrets
import time
import random
import string
from jinja2 import Template
import hashlib
# custom imports
import config

CREATE_NOTEBOOK_API_URL = "/api/notebook"
KEY = 'configuration'
ID_KEY = 'id'
LABEL_KEY = 'labels'
HOST_KEY = 'HAPROXY_0_VHOST'
COMMENT_KEY = 'comment'
LIBRARIES_KEY = 'libraries'
USERS_KEY = 'ZEPPELIN_SHIRO_CONF'
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
        try:
            instance_id = custom_configuration[ID_KEY]
        except KeyError:
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
        app_definition[ENV_KEY][USERS_KEY] = self._create_user_config_file(options["users"],
             options["usermanagement"]) if options["usermanagement"] != "no" else ""

        # Create entry for config store with only selected values
        metadata = {"comment": custom_configuration["comment"], "deleteAt": custom_configuration["deleteAt"],
                    KEY: {key: options[key] for key in  # this will copy most of the values of the "configuration" entry
                          [CPUS_KEY, ENV_KEY, MEM_KEY, "instances", "users", "usermanagement"]},
                    'url': INSTANCE_URL_PREFIX + instance_url, 'created_at': time.time(), 'id': instance_id,
                    "template_id": custom_configuration["template_id"]}
        metadata[KEY]["users"] = [] if options["usermanagement"] == "no" else metadata[KEY]["users"]  # remove users if no usermanagement
        metadata[KEY][LIBRARIES_KEY] = []
        for lib in custom_configuration[KEY][LIBRARIES_KEY]:  # libraries goes another level deeper
            try:
                metadata[KEY][LIBRARIES_KEY].append({key: lib[key] for key in {"language", "libraries", "tensorflow"}})
            except KeyError:
                metadata[KEY][LIBRARIES_KEY].append({key: lib[key] for key in {"language", "libraries"}})

        return app_definition, metadata

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
                    usermanagement == "random" and user["username"] == ""):
                # filter empty lines/users
                users.remove(user)
                continue
            if usermanagement == "random":
                user["password"] = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(20))
                # this password will be accessible outside the function because dict is a mutable type
            # hash passwords and store for template
            hashed_password = hashlib.sha256(user["password"].encode("utf-8")).hexdigest()
            hashed_users.append({"username": user["username"], "password": hashed_password})
        if len(users) is 0:
            # dont create a file if no users are to be created
            return ""
        else:
            with open("airfield/resources/shiro.ini.jinja2") as file_:
                template = Template(file_.read())
            out = template.render(users=hashed_users)
            return out

    def _generate_instance_id(self) -> str:
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(9))

    def _parse_url(self, instance_id: str) -> str:
        url = instance_id + config.BASE_HOST
        return url
