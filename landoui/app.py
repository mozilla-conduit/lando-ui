# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import logging
import logging.config
import os

import click
from flask import Flask
from flask_assets import Environment
from flask_talisman import Talisman
from webassets.loaders import YAMLLoader

from landoui import auth, errorhandlers
from landoui.helpers import str2bool
from landoui.logging import log_config_change, MozLogFormatter
from landoui.sentry import initialize_sentry

logger = logging.getLogger(__name__)

# This global is required to allow OIDC initialization on the entire app,
# yet still allow @oidc decorate uses for pages
oidc = None


def create_app(
    version_path,
    secret_key,
    session_cookie_name,
    session_cookie_domain,
    session_cookie_secure,
    use_https,
    enable_asset_pipeline,
    lando_api_url,
    debug=False
):
    """
    Create an app instance.
    """
    csp = {
        'default-src': "'self'",
        'font-src': "'self' https://code.cdn.mozilla.net",
        'style-src': "'self' https://code.cdn.mozilla.net",
        'img-src': "'self' *.cloudfront.net *.gravatar.com "
                   "*.googleusercontent.com",
        'object-src': "'none'",
        'frame-ancestors': "'none'",
        'manifest-src': "'none'",
        'worker-src': "'none'",
        'media-src': "'none'",
        'frame-src': "'none'",
        'base-uri': "'none'",
        'report-uri': "/__cspreport__"
    }  # yapf: disable

    initialize_logging()

    app = Flask(__name__)
    app.debug = debug

    # Set configuration
    app.config['VERSION_PATH'] = version_path
    log_config_change('VERSION_PATH', version_path)

    version_info = json.load(open(version_path))
    logger.info('application version', extra=version_info)

    this_app_version = version_info['version']
    initialize_sentry(app, this_app_version)

    app.config['LANDO_API_URL'] = lando_api_url
    log_config_change('LANDO_API_URL', lando_api_url)

    # Set remaining configuration
    app.config['SECRET_KEY'] = secret_key
    app.config['SESSION_COOKIE_NAME'] = session_cookie_name
    log_config_change('SESSION_COOKIE_NAME', session_cookie_name)
    app.config['SESSION_COOKIE_DOMAIN'] = session_cookie_domain
    log_config_change('SESSION_COOKIE_DOMAIN', session_cookie_domain)
    app.config['SESSION_COOKIE_SECURE'] = session_cookie_secure
    log_config_change('SESSION_COOKIE_SECURE', session_cookie_secure)
    app.config['SERVER_NAME'] = session_cookie_domain
    log_config_change('SERVER_NAME', session_cookie_domain)
    app.config['USE_HTTPS'] = use_https
    log_config_change('USE_HTTPS', use_https)
    app.config['PREFERRED_URL_SCHEME'] = 'https' if use_https else 'http'

    Talisman(app, content_security_policy=csp, force_https=use_https)

    # Authentication
    global oidc
    authentication = auth.OpenIDConnect(auth.OIDCConfig())
    oidc = authentication.auth(app)

    # Register routes via Flask Blueprints
    from landoui.pages import pages
    from landoui.revisions import revisions
    from landoui.dockerflow import dockerflow
    app.register_blueprint(pages)
    app.register_blueprint(revisions)
    app.register_blueprint(dockerflow)

    # Register template helpers
    from landoui.template_helpers import template_helpers
    app.register_blueprint(template_helpers)

    # Register error pages
    errorhandlers.register_error_handlers(app)

    # Setup Flask Assets
    assets = Environment(app)
    if enable_asset_pipeline:
        loader = YAMLLoader(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'assets_src/assets.yml'
            )
        )
        assets.register(loader.load_bundles())

    return app


def initialize_logging():
    """Initialize application-wide logging."""
    level = os.environ.get('LOG_LEVEL', 'INFO')
    logging.config.dictConfig(
        {
            'version': 1,
            'formatters': {
                'mozlog': {
                    '()': MozLogFormatter,
                    'mozlog_logger': 'lando-ui',
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'mozlog',
                },
                'null': {
                    'class': 'logging.NullHandler',
                }
            },
            'loggers': {
                'landoui': {
                    'level': level,
                    'handlers': ['console'],
                },
                'request.summary': {
                    'level': level,
                    'handlers': ['console'],
                },
                'flask': {
                    'handlers': ['null'],
                },
                'werkzeug': {
                    'level': 'ERROR',
                    'handlers': ['console'],
                },
            },
            'root': {
                'handlers': ['null'],
            },
            'disable_existing_loggers': True,
        }
    )
    logger.info('logging configured', extra={'LOG_LEVEL': level})


@click.command()
@click.option('--debug', envvar='DEBUG', type=bool, default=False)
@click.option('--host', envvar='HOST', default='0.0.0.0')
@click.option('--port', envvar='PORT', type=int, default=80)
@click.option(
    '--version-path', envvar='VERSION_PATH', default='/app/version.json'
)
@click.option('--secret-key', envvar='SECRET_KEY', default=None)
@click.option(
    '--session-cookie-name', envvar='SESSION_COOKIE_NAME', default=None
)
@click.option(
    '--session-cookie-domain', envvar='SESSION_COOKIE_DOMAIN', default=None
)
@click.option(
    '--session-cookie-secure', envvar='SESSION_COOKIE_SECURE', default=1
)
@click.option('--use-https', envvar='USE_HTTPS', default=1)
@click.option(
    '--enable-asset-pipeline', envvar='ENABLE_ASSET_PIPELINE', default=1
)
@click.option('--lando-api-url', envvar='LANDO_API_URL', default=None)
def run_dev_server(
    debug, host, port, version_path, secret_key, session_cookie_name,
    session_cookie_domain, session_cookie_secure, use_https,
    enable_asset_pipeline, lando_api_url
):
    """
    Run the development server which auto reloads when things change.
    """
    app = create_app(
        version_path, secret_key, session_cookie_name, session_cookie_domain,
        str2bool(session_cookie_secure),
        str2bool(use_https), enable_asset_pipeline, lando_api_url,
        str2bool(debug)
    )
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    app.run(debug=debug, port=port, host=host)
