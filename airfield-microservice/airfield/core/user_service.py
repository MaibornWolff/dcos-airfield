from app import oidc
from config import OIDC_ACTIVATED


class UserService(object):
    @staticmethod
    def get_user_name():
        # checks if oidc is activated and if the user is logged in, returns 'undefined' otherwise
        if UserService.user_loggedin():
            return oidc.user_getfield('preferred_username')
        return 'anonymous'

    @staticmethod
    def login_if_oidc(func):  # applies the decorator only if oidc is enabled
        if not OIDC_ACTIVATED:
            return func
        else:
            return oidc.require_login(func)

    @staticmethod
    def user_loggedin():
        return OIDC_ACTIVATED and oidc.user_loggedin