# -*- coding: utf-8 -*-
"""API routes for app interactions."""


#  standard import
import logging
# third party imports
from flask import Blueprint, render_template
# custom imports
from airfield.utility import ApiResponseStatus, ApiResponse
import config
from app import oidc


AppBlueprint = Blueprint('app', __name__)


@AppBlueprint.route('/')
def index():
    """
    Serves the frontend on the root path of the domain.

    :return: The static index.html file from the pre-built frontend.
    """
    return render_template('index.html')


@AppBlueprint.route('/security')
def get_security_level():
    response = ApiResponse()
    response.status = ApiResponseStatus.SUCCESS
    response.data = {'securityEnabled': config.OIDC_ACTIVATED}
    return response.to_json()


@AppBlueprint.route('/api/login')
@oidc.require_login
def api_login():
    """
    Allows users to authenticate themselves per OpenID Connect in order to use the API directly.
    The identification provider is configured on application start and needs to be specified in the
    proper environment variables. See 'config.py' for details.

    :return: An APIResponse object containing the currently valid authentication token.
    """
    response = ApiResponse()
    response.status = ApiResponseStatus.SUCCESS
    response.data = {'token': oidc.get_access_token()}
    return response.to_json()


@AppBlueprint.route('/api/logout')
def api_logout():
    response = ApiResponse()
    try:
        oidc.logout()
        response.status = ApiResponseStatus.SUCCESS
        response.data = {'Goodbye!'}
    except Exception as e:
        logging.error('Error in logout route={}'.format(e))
        response.status = ApiResponseStatus.INTERNAL_ERROR
        response.error_message = 'Authorization provider error.'
    return response.to_json()
