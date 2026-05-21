class RouterControllerError(Exception):
    pass


class NotConfiguredError(RouterControllerError):
    pass


class ConnectionError(RouterControllerError):
    pass


class AuthenticationError(RouterControllerError):
    pass
