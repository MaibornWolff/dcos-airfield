import json

from ..adapter.marathon import MarathonAdapter
from ..settings import config
from ..settings.base import JUPYTER_MARATHON_FILE
from ..util import dependency_injection as di
from ..util import metrics
from ..util.exception import HostNetworkException


class JupyterInstanceService:
    """Manage jupyter instances"""
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
    with open(JUPYTER_MARATHON_FILE) as marathon_file:
        app_definition = json.load(marathon_file)

    app_definition["id"] = app_id
    app_definition["cpus"] = int(configuration["notebook"]["cores"])
    app_definition["mem"] = int(configuration["notebook"]["memory"])
    env = app_definition["env"]

    if config.AIRFIELD_VIRTUAL_NETWORK_ENABLED:
        del app_definition["portDefinitions"]
        app_definition["networks"][0]["mode"] = "container"
        app_definition["networks"][0]["name"] = "dcos"
        app_definition["healthChecks"][0]["protocol"] = "MESOS_HTTP"
    else:
        del app_definition["container"]["portMappings"]
        app_definition["networks"][0]["mode"] = app_definition["container"]["network"] = "host"
        app_definition["healthChecks"][0]["protocol"] = "TCP"
        raise HostNetworkException("Currently a host network is not supported for jupyter instances! Please deploy a "
                                   "jupyter instance with an overlay network!")

    if config.JUPYTER_DOCKER_IMAGE:
        app_definition["container"]["docker"]["image"] = env["SPARK_EXECUTOR_DOCKER_IMAGE"] = config.JUPYTER_DOCKER_IMAGE

    env["JUPYTER_BASE_URL"] = app_definition["healthChecks"][0]["path"] = "/proxy/{}".format(app_id.split("/")[-1])
    env["SPARK_EXECUTOR_MEMORY"] = "{}m".format(configuration["spark"]["executor_memory"])
    env["SPARK_EXECUTOR_CORES"] = str(configuration["spark"]["executor_cores"])
    env["SPARK_TOTAL_EXECUTOR_CORES"] = str(configuration["spark"]["cores_max"])

    if configuration["usermanagement"]["enabled"]:
        env["JUPYTER_PASSWORD"] = configuration["usermanagement"]["password"]
        env["JUPYTER_DISABLE_PASSWORD"] = "false"
    else:
        env["JUPYTER_DISABLE_PASSWORD"] = "true"

    #  to provide communication via TLS (yet not possible for airfield)
    env["GEN_CERT"] = "false"


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
