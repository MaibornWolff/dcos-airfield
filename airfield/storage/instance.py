
from datetime import datetime
from ..adapter.kv import KVAdapter
from ..util import dependency_injection as di
from ..util.exception import InstanceRunningTimeException


BASE_KEY = "instances"
BASE_KEY_DELETED = "deleted_instances"


class InstanceStore:
    @di.inject
    def __init__(self, kv_adapter: KVAdapter):
        self._kv_adapter = kv_adapter

    def get_instance_ids(self, deleted=False):
        base_key = BASE_KEY if not deleted else BASE_KEY_DELETED
        instance_ids = list()
        for key, _ in self._kv_adapter.get_keys(base_key):
            instance_id = get_id_of_key(key)
            if instance_id not in instance_ids:
                instance_ids.append(instance_id)
        return instance_ids

    def get_instance(self, instance_id, deleted=False):
        base_key = BASE_KEY if not deleted else BASE_KEY_DELETED
        data = dict()
        for key, value in self._kv_adapter.get_keys("{}/{}".format(base_key, instance_id)):
            # The key is in the form 'instances/<instance_id>/configuration', so the last one is the searched one.
            data[key.split('/').pop()] = value
        return data

    def insert_instance(self, instance_id, configuration, metadata):
        self._kv_adapter.put_key("{}/{}/configuration".format(BASE_KEY, instance_id), configuration)
        self._kv_adapter.put_key("{}/{}/metadata".format(BASE_KEY, instance_id), metadata)
        self._kv_adapter.put_key("{}/{}/runtimes".format(BASE_KEY, instance_id), [])
        return dict(configuration=configuration, metadata=metadata)

    def update_instance_metadata(self, instance_id, metadata):
        self._kv_adapter.put_key("{}/{}/metadata".format(BASE_KEY, instance_id), metadata)

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
        if not runtimes:
            raise Exception("No runtime!")
        if runtimes[-1]["stopped_at"] is not None:
            raise InstanceRunningTimeException(f'The last runtime for the instance {instance_id} is already stopped!')
        runtimes[-1]["stopped_at"] = datetime.now().timestamp()
        self._kv_adapter.put_key("{}/{}/runtimes".format(BASE_KEY, instance_id), runtimes)

    def start_runtime(self, instance_id, cost_factors):
        runtimes = self._kv_adapter.get_key("{}/{}/runtimes".format(BASE_KEY, instance_id))
        if not runtimes:
            runtimes = []
        if len(runtimes) > 0 and runtimes[-1]["stopped_at"] is None:
            raise InstanceRunningTimeException(f'The last runtime for the instance {instance_id} is currently not stopped!')
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


def get_id_of_key(key):
    # The Last key part is 'configuration', 'metadata' and so on, so the key part before the last key part is the
    # searched one.
    return key.split('/')[-2]
