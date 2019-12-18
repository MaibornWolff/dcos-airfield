"""Simple dependency injection for singleton classes"""

from functools import wraps
from inspect import signature, Parameter


class _Registry:
    def __init__(self):
        self._instances = dict()

    def get(self, cls):
        if cls not in self._instances:
            self._instances[cls] = cls()
        return self._instances[cls]

    def register(self, cls, instance):
        self._instances[cls] = instance

    def clear(self):
        self._instances.clear()


_registry = _Registry()


def register(cls, instance):
    _registry.register(cls, instance)


def get(cls):
    return _registry.get(cls)


def inject(fn):
    sig = signature(fn)
    @wraps(fn)
    def wrapped_init(self, *outer_args, **kwargs):
        # Override injection if arguments are provided
        if outer_args:
            return fn(self, *outer_args)
        args = list()
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            if param.annotation is Parameter.empty:
                raise Exception("No type annotation for {} in {}".format(name, self.__class__.__name__))
            if name in kwargs:
                args.append(kwargs[name])
            else:
                args.append(_registry.get(param.annotation))
        return fn(self, *args)
    return wrapped_init


def context(fn):
    """Reset injection registry after context finishes"""
    @wraps(fn)
    def wrapped_method(self):
        _registry.clear()
        fn(self)
        _registry.clear()
    return wrapped_method


def test_setup_clear_registry():
    _registry.clear()