from config import OIDC_ACTIVATED
from . import airfield_service
from . import UserService


class AuthService(object):
    @staticmethod
    def is_loggedin_user_authorized(allowed_users):
        if not OIDC_ACTIVATED:
            return True
        actual_user = UserService.get_user_name().upper()
        for user in allowed_users:
            if user['username'].upper() == actual_user:
                return True
        return False

    @staticmethod
    def check_for_authorisation(instance_id):
        # only for oidc authorisation
        if not OIDC_ACTIVATED:  # oidc is not activated so everyone is allowed
            return True
        instance = airfield_service.get_existing_zeppelin_instance(instance_id)
        if instance is None:  # the requested instance does not exist
            return True
        options = instance['configuration']
        if options['usermanagement'] != 'oidc':  # another usermanagment is choosen
            return True
        if not AuthService.is_loggedin_user_authorized(options['users']) and UserService.get_user_name().upper() != instance['createdBy'].upper():
            raise Exception(f'ERROR 401: The User {UserService.get_user_name()} is not allowed to request for the '
                            f'instance {instance_id} created by {instance["createdBy"]}!')
