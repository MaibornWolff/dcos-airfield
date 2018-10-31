# -*- coding: utf-8 -*-
"""
Entry point for the Flask Application.

Tasks:
1. Configure logging
2. Create application object and enable CORS
3. Validate and apply configuration
4. Register the API through flask blueprints
5. Register error handlers and their corresponding Prometheus metrics
"""


#  standard import
import sys
import logging
# third party imports
from flask_cors import CORS
from flask_api import FlaskAPI
from flask_oidc import OpenIDConnect
from prometheus_client import Counter
from flask_log_request_id import RequestID, RequestIDLogFilter
# custom imports
import config

oidc = OpenIDConnect()

airfield_http_error_metric = Counter('airfield_http_errors_total', 'HTTP Errors', ['type'])


def create_app():
    logging.getLogger().setLevel(config.LOGGING_LEVEL)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(config.LOGGING_LEVEL)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - level=%(levelname)s - request_id=%(request_id)s - %(message)s')
    )
    handler.addFilter(RequestIDLogFilter())
    logging.getLogger().addHandler(handler)
    logging.info('Configured logging to stdout.')
    logging.info('Starting Flask application...')
    app = FlaskAPI(__name__,
                   static_folder=config.STATIC_FOLDER,
                   template_folder=config.TEMPLATE_FOLDER,
                   instance_relative_config=True)
    logging.info('Flask application started.')
    logging.info('Validating configuration...')
    try:
        app.config.from_object(config)
    except KeyError as e:
        logging.error(e)
        sys.exit(-1)
    logging.info('Config is valid...')
    logging.info('Configuring CORS...')
    CORS(app)
    logging.info('CORS configured.')
    logging.info('Configuring RequestID...')
    RequestID(app)
    logging.info('RequestID configured.')
    logging.info('Registering application blueprints...')
    from airfield.api import ZeppelinBlueprint, AppBlueprint
    app.register_blueprint(AppBlueprint)
    app.register_blueprint(ZeppelinBlueprint,
                           url_prefix=config.API_PREFIX)
    logging.info('Application blueprints registered.')
    logging.info('Registering error handlers and metrics...')

    @AppBlueprint.errorhandler(500)
    def handle_500(error):
        logging.error('{}'.format(error))
        airfield_http_error_metric.labels(type='500').inc()
        return str(error), 500

    @app.errorhandler(404)
    def handle_404(error):
        logging.warning('{}'.format(error))
        airfield_http_error_metric.labels(type='404').inc()
        return str(error), 404

    @app.errorhandler(401)
    def handle_401(error):
        logging.warning('{}'.format(error))
        airfield_http_error_metric.labels(type='401').inc()
        return str(error), 401

    @app.errorhandler(405)
    def handle_405(error):
        logging.warning('{}'.format(error))
        airfield_http_error_metric.labels(type='405').inc()
        return str(error), 405
    logging.info('Error handlers and metrics registered.')

    return app
