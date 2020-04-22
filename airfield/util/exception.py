"""Exception types used by airfield"""


class InstanceTypeError(Exception):
    def __init__(self, error):
        super().__init__()
        self.error = error


class ConfigurationException(Exception):
    def __init__(self, error):
        super().__init__()
        self.error = error


class InstanceRunningTimeException(Exception):
    def __init__(self, error):
        super().__init__()
        self.error = error


class ConflictError(Exception):
    def __init__(self, error):
        super().__init__()
        self.error = error


class TechnicalException(Exception):
    pass


class HostNetworkException(Exception):
    def __init__(self, error):
        super().__init__()
        self.error = error
