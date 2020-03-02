from ..settings.config import OIDC_ACTIVATED, DCOS_GROUPS_ENABLED, DCOS_GROUPS_MAPPING
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


def get_user_groups():
    groups = list()
    if OIDC_ACTIVATED:
        groups = oidc.user_getfield('user_groups') or list()
        groups = list(map(lambda g: g[1:] if g.startswith('/') else g, groups))
    return groups


def get_airfield_groups():
    return list(DCOS_GROUPS_MAPPING.keys())


def get_available_groups():
    available_groups = list()
    if OIDC_ACTIVATED:
        groups = get_user_groups()
        for group in get_airfield_groups():
            if group in groups:
                available_groups.append(group)
    return available_groups


def get_dcos_settings():
    if OIDC_ACTIVATED:
        return {
            'groups': get_available_groups(),
            'oidc_activated': OIDC_ACTIVATED,
            'dcos_groups_activated': DCOS_GROUPS_ENABLED
        }
    else:
        return {
            'groups': [],
            'oidc_activated': OIDC_ACTIVATED,
            'dcos_groups_activated': DCOS_GROUPS_ENABLED
        }