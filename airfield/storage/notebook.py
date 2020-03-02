
from ..adapter.kv import KVAdapter
from ..util import dependency_injection as di


BASE_KEY = "notebooks"


class NotebookStore:
    @di.inject
    def __init__(self, kv_adapter: KVAdapter):
        self._kv_adapter = kv_adapter

    def get_notebooks(self, instance_type="zeppelin"):
        notebooks = list()
        for key, value in self._kv_adapter.get_keys(BASE_KEY):
            if value["type"] != instance_type:
                continue
            notebooks.append(dict(id=_get_id_of_key(key), name=value["name"]))
        return notebooks

    def get_notebook(self, notebook_id):
        data = self._kv_adapter.get_key("{}/{}".format(BASE_KEY, notebook_id))
        return data

    def find_notebook(self, instance_type, name):
        for key, value in self._kv_adapter.get_keys(BASE_KEY):
            if value["type"] != instance_type:
                continue
            if value["name"] == name:
                return _get_id_of_key(key)
        return None

    def delete_notebook(self, notebook_id):
        self._kv_adapter.delete_key("{}/{}".format(BASE_KEY, notebook_id))

    def store_notebook(self, notebook_id, name, notebook_data, username):
        self._kv_adapter.put_key("{}/{}".format(BASE_KEY, notebook_id), dict(type="zeppelin", name=name, data=notebook_data, creator=username))


def _get_id_of_key(key):
    return key.split('/').pop()
