"""Logging utils"""

import logging
import sys
from flask_log_request_id import RequestIDLogFilter
from ..settings import config


def _init_logger():
    logger = logging.getLogger()
    logger.setLevel(config.LOGGING_LEVEL)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(config.LOGGING_LEVEL)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - level=%(levelname)s - request_id=%(request_id)s - %(message)s'))
    handler.addFilter(RequestIDLogFilter())
    logger.addHandler(handler)
    return logger


def silence():
    logger.setLevel("CRITICAL")


logger = _init_logger()
