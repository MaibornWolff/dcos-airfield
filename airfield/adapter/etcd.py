"""Wrapper for etcd interactions."""

import json
import etcd
from ..settings import config
from ..util import metrics
from ..util.logging import logger
from ..util.exception import TechnicalException


class EtcdAdapter(object):
    def __init__(self):
        logger.info('Initializing EtcdAdapter')
        endpoint = config.ETCD_ENDPOINT
        protocol = "http"
        version_prefix = '/v2'
        if "://" in endpoint:
            protocol, endpoint = endpoint.split("://")
        if "/" in endpoint:
            list = endpoint.split("/")
            endpoint = list[0]
            version_prefix = '/' + list[1]
        if ":" not in endpoint:
            host, port = endpoint, 2379
        else:
            host, port = endpoint.split(":")
        self._client = etcd.Client(host=host, port=int(port), protocol=protocol, version_prefix=version_prefix)
        self._error_metric = metrics.Counter("airfield_etcd_request_errors", "Number of errors encountered with etcd", [])

    def get_key(self, key):
        try:
            result = self._client.read(self._build_key(key))
            if result and result.value:
                return json.loads(result.value)
            else:
                return None
        except etcd.EtcdKeyNotFound:
            return None
        except Exception as e:
            logger.error(e)
            self._error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def get_keys(self, key):
        try:
            for child in self._client.read(self._build_key(key)).children:
                yield child.key, (json.loads(child.value) if child.value else None)
        except etcd.EtcdKeyNotFound:
            return
        except Exception as e:
            logger.error(e)
            self._error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def put_key(self, key, value):
        try:
            self._client.write(self._build_key(key), json.dumps(value))
        except Exception as e:
            logger.error(e)
            self._error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def delete_key(self, key, recursive=False):
        try:
            self._client.delete(self._build_key(key), recursive=recursive)
        except Exception as e:
            logger.error(e)
            self._error_metric.inc()
            raise TechnicalException("etcd server cannot be reached.")

    def _build_key(self, key):
        return "{}/{}".format(config.CONFIG_BASE_KEY, key)


    