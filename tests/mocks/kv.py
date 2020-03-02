
class InMemoryKVAdapter:
    """ Dummy in-memory key-value store to be used as mock for KVAdapter"""
    def __init__(self):
        self._data = {}

    def get_key(self, key):
        root, key = self._navigate(key)
        return root.get(key, None)

    def get_keys(self, key):
        root, key = self._navigate(key)
        for sub_key in list(root.keys()):
            if sub_key.startswith(key):
                yield sub_key, root.get(sub_key)

    def put_key(self, key, value):
        root, key = self._navigate(key)
        root[key] = value

    def delete_key(self, key, recursive=False):
        root, key = self._navigate(key)
        for sub_key in list(root.keys()):
            if sub_key.startswith(key):
                root.pop(sub_key)

    def _navigate(self, key):
        root = self._data
        return root, key


