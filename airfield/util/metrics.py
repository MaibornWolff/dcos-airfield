"""Common used metrics with simple wrappers for easier use"""

from prometheus_client import Gauge, Counter, Summary


_metric_api_endpoint_summary = Summary("airfield_api_endpoint", "", ["endpoint", "method"])
_metric_service_method_summary = Summary("airfield_service_method", "", ["component", "method"])


def api_endpoint(endpoint, method=None):
    """Decorator for api endpoints so they get timed"""
    if not method:
        method = "GET"
    return _metric_api_endpoint_summary.labels(endpoint, method).time()


def instrument(func):
    component, method = func.__qualname__.rsplit(".", 1)
    return _metric_service_method_summary.labels(component, method).time()(func)


def service_method(component, method):
    return _metric_service_method_summary.labels(component, method).time()
