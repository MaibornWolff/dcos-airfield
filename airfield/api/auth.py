from ..settings.config import OIDC_ACTIVATED, DCOS_GROUPS_ENABLED
from . import oidc


def get_user_name():
    """Return the username of the currently logged in user or 'anonymous' if oidc is deactivated"""
    if _user_loggedin():
        return oidc.user_getfield('preferred_username')
    return 'anonymous'


def require_login(func):
    """Apply the oidc.require_login decorator only if oidc is activated"""
    if not OIDC_ACTIVATED:
        return func
    else:
        return oidc.require_login(func)


def _user_loggedin():
    return OIDC_ACTIVATED and oidc.user_loggedin


def user_groups():
    if OIDC_ACTIVATED:
        groups = oidc.user_getfield('user_groups')
        for group in groups:
            if group.startswith('/'):
                group = group[1:]
        return {
            'groups': groups,
            'oidc_activated': OIDC_ACTIVATED,
            'dcos_groups_activated': DCOS_GROUPS_ENABLED
        }
    else:
        return {
            'groups': [],
            'oidc_activated': OIDC_ACTIVATED,
            'dcos_groups_activated': DCOS_GROUPS_ENABLED
        }