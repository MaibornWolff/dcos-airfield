# -*- coding: utf-8 -*-
"""API routes for app interactions."""


# standard import
import logging
# third party imports
from flask import Blueprint, render_template, redirect, send_from_directory
from prometheus_client import generate_latest, Counter
# custom imports
from airfield.utility import ApiResponseStatus, ApiResponse
import config
from app import oidc

airfield_requests_metrics = Counter('airfield_login_requests', 'Login Requests', ['endpoint'])
AppBlueprint = Blueprint('app', __name__)


@AppBlueprint.route('/')
def index():
    """
    Serves the frontend on the root path of the domain.

    :return: The static index.html file from the pre-built frontend.
    """
    return render_template('index.html')


@AppBlueprint.route('/favicon.ico')
def favicon():
    return send_from_directory(config.TEMPLATE_FOLDER, 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@AppBlueprint.route('/api/security')
def login_state():
    """
    Allows users to authenticate themselves via OpenID Connect in order to use the API directly.
    The identification provider is configured on application start and needs to be specified in the
    proper environment variables. See 'config.py' for details.

    :return: An APIResponse object containing the authentication status and username.
    """
    airfield_requests_metrics.labels(endpoint='/api/security').inc()
    response = ApiResponse()
    response.status = ApiResponseStatus.SUCCESS
    response.data = {'isAuthenticated': oidc.user_loggedin if config.OIDC_ACTIVATED else False,
                     'authentication': bool(config.OIDC_ACTIVATED),
                     'username': oidc.user_getfield('preferred_username') if config.OIDC_ACTIVATED and oidc.user_loggedin else ''}
    return response.to_json()


@AppBlueprint.route('/login')
@oidc.require_login
def login_redirect():
    """
    Redirect to login first and then back to the frontend if login was successful.
    All requests from then on will be authenticated by an httpOnly cookie

    :return: A redirect code to the home page of the frontend
    """
    airfield_requests_metrics.labels(endpoint='/login').inc()
    return redirect("/", code=302)


@AppBlueprint.route('/logout')
@oidc.require_login
def api_logout():
    """
    Logout the currently logged in user

    :return: A redirect code to the home page of the frontend
    """
    airfield_requests_metrics.labels(endpoint='/logout').inc()
    try:
        oidc.logout()
        return redirect("/", code=302)
    except Exception as e:
        response = ApiResponse()
        logging.error('Error in logout route={}'.format(e))
        response.status = ApiResponseStatus.INTERNAL_ERROR
        response.error_message = 'Authorization provider error.'
        return response.to_json()
