"""Generic KeyValue Store adapter that delegates calls to an actual implementation depending on configuration"""

from .etcd import EtcdAdapter
from .consul import ConsulAdapter
from ..settings import config
from ..util import dependency_injection as di


class KVAdapter:
    def __init__(self):
        if config.ETCD_ENDPOINT:
            self._kv = di.get(EtcdAdapter)
        elif config.CONSUL_ENDPOINT:
            self._kv = di.get(ConsulAdapter)
        else:
            raise Exception("No key-value-store configured")

    def get_key(self, key):
        return self._kv.get_key(key)

    def get_keys(self, key):
        yield from self._kv.get_keys(key)

    def put_key(self, key, value):
        return self._kv.put_key(key, value)

    def delete_key(self, key, recursive=False):
        return self._kv.delete_key(key, recursive=recursive)
