"""API routes for app interactions."""

from flask import Blueprint, render_template, redirect, send_from_directory, Response
from prometheus_client import generate_latest
from ..settings import config
from ..settings.base import APP_STATIC_FOLDER
from ..util import metrics
from ..util.logging import logger
from . import oidc, auth


app_blueprint = Blueprint('app', __name__, static_folder=APP_STATIC_FOLDER, template_folder=APP_STATIC_FOLDER)


def register_blueprint(app):
    app.register_blueprint(app_blueprint)


@app_blueprint.route('/')
@metrics.api_endpoint("/")
def index():
    """
    Serves the frontend on the root path of the domain.
    """
    return render_template('index.html')


@app_blueprint.route('/favicon.ico')
def favicon():
    return send_from_directory(APP_STATIC_FOLDER, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app_blueprint.route('/api/security/state')
@metrics.api_endpoint("/api/security/state")
def login_state():
    """
    Allows users to authenticate themselves via OpenID Connect in order to use the API directly.
    The identification provider is configured on application start and needs to be specified in the
    proper environment variables. See 'config.py' for details.
    """
    return {'isAuthenticated': oidc.user_loggedin if config.OIDC_ACTIVATED else False,
            'authentication': config.OIDC_ACTIVATED,
            'username': oidc.user_getfield('preferred_username') if config.OIDC_ACTIVATED and oidc.user_loggedin else ''}


@app_blueprint.route('/api/security/groups')
@metrics.api_endpoint("/api/security/groups")
def security_groups():
    """
    Returns a list of groups the user has in keycloak
    """
    return auth.user_groups()


@app_blueprint.route('/login')
@metrics.api_endpoint("/login")
@oidc.require_login
def login_redirect():
    """
    Redirect to login first and then back to the frontend if login was successful.
    All requests from then on will be authenticated by an httpOnly cookie
    """
    return redirect("/", code=302)


@app_blueprint.route('/logout')
@metrics.api_endpoint("/logout")
@oidc.require_login
def api_logout():
    """
    Logout the currently logged in user and redirect to the homepage
    """
    try:
        oidc.logout()
        return redirect("/", code=302)
    except Exception as e:
        logger.error('Error in logout route={}'.format(e))
        return dict(msg='Authorization provider error'), 500


@app_blueprint.route('/metrics', methods=['GET'])
def get_metrics():
    return Response(generate_latest())


@app_blueprint.errorhandler(500)
def handle_500(error):
    logger.error('{}'.format(error))
    return dict(msg="Internal server error"), 500


@app_blueprint.errorhandler(404)
def handle_404(error):
    logger.warning('{}'.format(error))
    return dict(msg="Page not found"), 404


@app_blueprint.errorhandler(401)
def handle_401(error):
    logger.warning('{}'.format(error))
    return dict(msg="Authorization required"), 401


@app_blueprint.errorhandler(405)
def handle_405(error):
    logger.warning('{}'.format(error))
    return dict(msg="Method not supported"), 405