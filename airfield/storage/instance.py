
from datetime import datetime
from ..adapter.kv import KVAdapter
from ..util import dependency_injection as di


BASE_KEY = "instances"
BASE_KEY_DELETED = "deleted_instances"


class InstanceStore:
    @di.inject
    def __init__(self, kv_adapter: KVAdapter):
        self._kv_adapter = kv_adapter

    def get_instance_ids(self, deleted=False):
        base_key = BASE_KEY if not deleted else BASE_KEY_DELETED
        return [key for key, _ in self._kv_adapter.get_keys(base_key)]

    def get_instance(self, instance_id, deleted=False):
        base_key = BASE_KEY if not deleted else BASE_KEY_DELETED
        data = dict()
        for key, value in self._kv_adapter.get_keys("{}/{}".format(base_key, instance_id)):
            data[key] = value
        return data

    def insert_instance(self, instance_id, configuration, metadata):
        self._kv_adapter.put_key("{}/{}/configuration".format(BASE_KEY, instance_id), configuration)
        self._kv_adapter.put_key("{}/{}/metadata".format(BASE_KEY, instance_id), metadata)
        self._kv_adapter.put_key("{}/{}/runtimes".format(BASE_KEY, instance_id), [])
        return dict(configuration=configuration, metadata=metadata)

    def update_instance_configuration(self, instance_id, configuration):
        self._kv_adapter.put_key("{}/{}/configuration".format(BASE_KEY, instance_id), configuration)
        return self.get_instance(instance_id)

    def delete_instance(self, instance_id):
        configuration = self._kv_adapter.get_key("{}/{}/configuration".format(BASE_KEY, instance_id))
        metadata = self._kv_adapter.get_key("{}/{}/metadata".format(BASE_KEY, instance_id))
        runtimes = self._kv_adapter.get_key("{}/{}/runtimes".format(BASE_KEY, instance_id))
        self._kv_adapter.put_key("{}/{}/configuration".format(BASE_KEY_DELETED, instance_id), configuration)
        self._kv_adapter.put_key("{}/{}/runtimes".format(BASE_KEY_DELETED, instance_id), runtimes)
        self._kv_adapter.put_key("{}/{}/metadata".format(BASE_KEY_DELETED, instance_id), metadata)
        self._kv_adapter.delete_key("{}/{}".format(BASE_KEY, instance_id), recursive=True)

    def store_extra_data(self, instance_id, name, data):
        self._kv_adapter.put_key("{}/{}/{}".format(BASE_KEY, instance_id, name), data)

    def get_extra_data(self, instance_id, name):
        return self._kv_adapter.get_key("{}/{}/{}".format(BASE_KEY, instance_id, name))

    def delete_extra_data(self, instance_id, name):
        self._kv_adapter.delete_key("{}/{}/{}".format(BASE_KEY, instance_id, name))

    def finish_runtime(self, instance_id):
        runtimes = self._kv_adapter.get_key("{}/{}/runtimes".format(BASE_KEY, instance_id))
        if not runtimes or runtimes[-1]["stopped_at"] is not None:
            raise Exception("No unfinished runtime")
        runtimes[-1]["stopped_at"] = datetime.now().timestamp()
        self._kv_adapter.put_key("{}/{}/runtimes".format(BASE_KEY, instance_id), runtimes)

    def start_runtime(self, instance_id, cost_factors):
        runtimes = self._kv_adapter.get_key("{}/{}/runtimes".format(BASE_KEY, instance_id))
        if not runtimes:
            runtimes = []
        runtime = _runtime_model.copy()
        runtime["started_at"] = datetime.now().timestamp()
        runtime["cores"] = cost_factors["cores"]
        runtime["memory"] = cost_factors["memory"]
        runtimes.append(runtime)
        self._kv_adapter.put_key("{}/{}/runtimes".format(BASE_KEY, instance_id), runtimes)


_runtime_model = {
    "started_at": None,
    "stopped_at": None,
    "cores": 0,
    "memory": 0,
}