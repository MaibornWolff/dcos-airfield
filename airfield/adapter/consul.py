"""Wrapper for consul interactions."""

import json
from urllib.error import URLError, HTTPError
from consul_kv import Connection
from ..settings import config
from ..util import metrics
from ..util.logging import logger
from ..util.exception import TechnicalException


class ConsulAdapter(object):
    def __init__(self):
        logger.info('Initializing ConsulAdapter')
        self._con = Connection(endpoint=config.CONSUL_ENDPOINT)
        self._error_metric = metrics.Counter("airfield_consul_request_errors", "Number of errors encountered with consul", [])

    def get_key(self, key):
        key = self._build_key(key)
        try:
            return json.loads(self._con.get(key)[key])
        except URLError as e:
            if isinstance(e, HTTPError) and e.code == 404:
                return None
            logger.error(e)
            self._error_metric.inc()
            raise TechnicalException("Consul server cannot be reached.")

    def get_keys(self, key):
        key = self._build_key(key)
        try:
            result = self._con.get(key, recurse=True)
            for sub_key, sub_value in result.items():
                yield sub_key, json.loads(sub_value)
        except URLError as e:
            if isinstance(e, HTTPError) and e.code == 404:
                return
            logger.error(e)
            self._error_metric.inc()
            raise TechnicalException("Consul server cannot be reached.")

    def put_key(self, key, value):
        key = self._build_key(key)
        try:
            self._con.put(key, json.dumps(value))
        except URLError as e:
            logger.error(e)
            self._error_metric.inc()
            raise TechnicalException("Consul server cannot be reached.")

    def delete_key(self, key, recursive=False):
        key = self._build_key(key)
        try:
            self._con.delete(key, recurse=recursive)
            return True
        except URLError as e:
            if isinstance(e, HTTPError) and e.code == 404:
                return False
            logger.error(e)
            self._error_metric.inc()
            raise TechnicalException("Consul server cannot be reached.")

    def _build_key(self, key):
        return "{}/{}".format(config.CONFIG_BASE_KEY, key)
