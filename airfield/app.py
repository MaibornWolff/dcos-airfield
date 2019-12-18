import base64
from flask_cors import CORS
from flask_api import FlaskAPI
from flask_log_request_id import RequestID
from .api import main, oidc
from .service.cleanup import InstanceCleanupService
from .settings import config, base
from .util import dependency_injection as di
from .util.logging import logger


def create_app():
    logger.info('Starting Flask application...')
    app = FlaskAPI(__name__, static_folder=base.APP_STATIC_FOLDER, template_folder=base.APP_STATIC_FOLDER, instance_relative_config=True)
    app.config.from_object(config)
    app.config.from_object(base)
    if config.OIDC_ACTIVATED:
        logger.info('Activating OpenID Connect...')
        if config.OIDC_CLIENT_SECRETS_BASE64 is not None:
            with open(config.OIDC_CLIENT_SECRETS, "wb") as oidc_secrets_file:
                oidc_secrets_file.write(base64.b64decode(config.OIDC_CLIENT_SECRETS_BASE64))
        oidc.init_app(app)
        logger.info('OpenID Connect activated.')
    logger.info('Configuring CORS...')
    CORS(app)
    logger.info('CORS configured.')
    logger.info('Configuring RequestID...')
    RequestID(app)
    logger.info('Registering APIs...')
    main.register_blueprints(app)
    logger.info('Flask app prepared.')
    # Init here so service can start its scheduler
    di.get(InstanceCleanupService)
    return app