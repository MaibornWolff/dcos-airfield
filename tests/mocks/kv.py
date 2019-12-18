
class InMemoryKVAdapter:
    """ Dummy in-memory key-value store to be used as mock for KVAdapter"""
    def __init__(self):
        self._data = {}

    def get_key(self, key):
        root, key = self._navigate(key)
        return root.get(key, None)

    def get_keys(self, key):
        root, key = self._navigate(key)
        for sub_key, sub_value in root.get(key, dict()).items():
            yield sub_key, sub_value

    def put_key(self, key, value):
        root, key = self._navigate(key)
        root[key] = value

    def delete_key(self, key, recursive=False):
        root, key = self._navigate(key)
        root.pop(key, None)

    def _navigate(self, key):
        root = self._data
        parts = key.split("/")
        for part in parts[:-1]:
            if part not in root:
                root[part] = dict()
            root = root[part]
        return root, parts[-1]


