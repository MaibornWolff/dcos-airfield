
import hashlib
import json
from jinja2 import Template
from ..adapter.marathon import MarathonAdapter
from ..settings import config
from ..settings.base import ZEPPELIN_MARATHON_FILE, SHIRO_CONF_FILE
from ..util import dependency_injection as di
from ..util import metrics


class ZeppelinInstanceService:
    """Manage zeppelin instances"""
    @di.inject
    def __init__(self, marathon_adapter: MarathonAdapter):
        self._marathon_adapter = marathon_adapter

    @metrics.instrument
    def create_instance(self, instance_path, configuration):
        marathon_app_definition = _generate_marathon_configuration(instance_path, configuration)
        self._marathon_adapter.deploy_instance(marathon_app_definition)

    @metrics.instrument
    def update_instance(self, instance_path, configuration):
        marathon_app_definition = _generate_marathon_configuration(instance_path, configuration)
        self._marathon_adapter.deploy_instance(marathon_app_definition)

    @metrics.instrument
    def delete_instance(self, instance_path):
        self._marathon_adapter.delete_instance(instance_path)


def _generate_marathon_configuration(app_id, configuration):
    with open(ZEPPELIN_MARATHON_FILE) as marathon_file:
        app_definition = json.load(marathon_file)

    app_definition["id"] = app_id
    app_definition["cpus"] = int(configuration["notebook"]["cores"])
    app_definition["mem"] = int(configuration["notebook"]["memory"])

    app_definition["env"]["SPARK_EXECUTOR_MEMORY"] = "{}m".format(configuration["spark"]["executor_memory"])
    app_definition["env"]["SPARK_EXECUTOR_CORES"] = str(configuration["spark"]["executor_cores"])
    app_definition["env"]["SPARK_CORES_MAX"] = str(configuration["spark"]["cores_max"])
    app_definition["env"]["PYSPARK_PYTHON"] = configuration["spark"]["python_version"]

    if config.ZEPPELIN_DOCKER_IMAGE:
        app_definition["container"]["docker"]["image"] = config.ZEPPELIN_DOCKER_IMAGE
    if config.SPARK_MESOS_EXECUTOR_DOCKER_IMAGE:
        app_definition["env"]["SPARK_MESOS_EXECUTOR_DOCKER_IMAGE"] = config.SPARK_MESOS_EXECUTOR_DOCKER_IMAGE

    python_packages_string, r_packages_string = _parse_additional_packages(configuration)
    if python_packages_string:
        app_definition["env"]["PYTHON_PACKAGES"] = python_packages_string
    if r_packages_string:
        app_definition["env"]["R_PACKAGES"] = r_packages_string
    app_definition["env"]["ZEPPELIN_SHIRO_CONF"] = _create_user_config_file(configuration)

    if config.HDFS_CONFIG_FOLDER:
        hdfs_folder = config.HDFS_CONFIG_FOLDER
        if "://" not in hdfs_folder:
            hdfs_folder = "http://" + hdfs_folder
        app_definition["fetch"] = [{
            "uri": hdfs_folder + "/hdfs-site.xml",
            "extract": False,
            "executable": False,
            "cache": False
        }, {
            "uri": hdfs_folder + "/core-site.xml",
            "extract": False,
            "executable": False,
            "cache": False
        }]
    return app_definition
    

def _parse_additional_packages(configuration: dict):
    """
    Airfield allows for additional R/Python packages to be defined.
    These are passed into the required format for installation here.

    :param configuration: dictionary containing the configuration
    :return: the configuration with added packages
    """
    python_packages_string = _create_python_packages_string(configuration["libraries"]["python"])
    r_packages_string = _create_r_packages_string(configuration["libraries"]["r"])
    return python_packages_string, r_packages_string


def _create_python_packages_string(python_packages: list):
    """
    Builds the specific string required by Zeppelin images to install Python packages.

    :param python_packages: list containing Python package strings
    :return: the properly formatted Python packages string
    """
    if len(python_packages) == 0:
        return None
    else:
        return " ".join(python_packages)


def _create_r_packages_string(r_packages: list):
    """
    Builds the specific string required by Zeppelin images to install R packages.

    :param r_packages: list containing R package strings
    :return: the properly formatted R packages string
    """
    if len(r_packages) == 0:
        return None
    else:
        package_string = ','.join(["'%s'" % p for p in r_packages])
        return "c(%s)" % package_string


def _create_user_config_file(configuration: dict):
    usermanagement = configuration["usermanagement"]
    if not usermanagement["enabled"]:
        return ""
    hashed_users = []
    for user, password in usermanagement["users"].items():
        if not user:
            continue
        # hash passwords and store for template
        hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        hashed_users.append({"username": user, "password": hashed_password})
    with open(SHIRO_CONF_FILE) as shiro_file:
        template = Template(shiro_file.read())
    out = template.render(users=hashed_users)
    return out