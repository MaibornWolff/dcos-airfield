from config import OIDC_ACTIVATED
from . import airfield_service
from . import UserService
from airfield.utility import ApiResponse, ApiResponseStatus


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
    def check_for_authorisation(instance_id) -> ApiResponse:
        # only for oidc authorisation
        result = ApiResponse()
        if not OIDC_ACTIVATED:  # oidc is not activated so everyone is allowed
            result.status = ApiResponseStatus.SUCCESS
            return result
        instance = airfield_service.get_existing_zeppelin_instance(instance_id)
        if instance is None:  # the requested instance does not exist
            result.status = ApiResponseStatus.SUCCESS
            return result
        options = instance['configuration']
        if options['usermanagement'] != 'oidc':  # another usermanagment is choosen
            result.status = ApiResponseStatus.SUCCESS
            return result
        if (not AuthService.is_loggedin_user_authorized(options['users'])) and UserService.get_user_name().upper() != instance['createdBy'].upper():
            result.status = ApiResponseStatus.UNAUTHORIZED
            result.error_message = f'The user {UserService.get_user_name()} is not allowed to request the instance {instance_id}!'
            return result
