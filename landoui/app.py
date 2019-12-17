# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import logging
import logging.config
import os
from urllib.parse import urlparse

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
    app.config['BUGZILLA_URL'] = _lookup_service_url(lando_api_url, 'bugzilla')
    log_config_change('BUGZILLA_URL', app.config['BUGZILLA_URL'])
    app.config['PHABRICATOR_URL'] = (
        _lookup_service_url(lando_api_url, 'phabricator')
    )
    log_config_change('PHABRICATOR_URL', app.config['PHABRICATOR_URL'])
    app.config['ENABLE_SEC_APPROVAL'] = bool(os.getenv('ENABLE_SEC_APPROVAL'))
    log_config_change('ENABLE_SEC_APPROVAL', app.config['ENABLE_SEC_APPROVAL'])
    app.config['ENABLE_EMBEDDED_TRANSPLANT_UI'] = (
        bool(os.getenv('ENABLE_EMBEDDED_TRANSPLANT_UI'))
    )
    log_config_change(
        'ENABLE_EMBEDDED_TRANSPLANT_UI',
        app.config['ENABLE_EMBEDDED_TRANSPLANT_UI']
    )

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
    from landoui.secapproval import secapproval
    app.register_blueprint(pages)
    app.register_blueprint(revisions)
    app.register_blueprint(dockerflow)
    app.register_blueprint(secapproval)

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

    logger.info("Application started successfully.")
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
@click.option(
    '--reload/--no-reload',
    default=None,
    help='Enable or disable the reloader. By default the reloader '
    'is active if debug is enabled.'
)
@click.option(
    '--debugger/--no-debugger',
    default=None,
    help='Enable or disable the debugger. By default the debugger '
    'is active if debug is enabled.'
)
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
    debug, reload, debugger, host, port, version_path, secret_key,
    session_cookie_name, session_cookie_domain, session_cookie_secure,
    use_https, enable_asset_pipeline, lando_api_url
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

    app.run(
        debug=debug,
        port=port,
        host=host,
        use_reloader=reload,
        use_debugger=debug
    )


def _lookup_service_url(lando_api_url, service_name):
    # TODO: Restructure things to pull this information from lando-api
    # itself / lookup like other environment variables. Sticking this here
    # is a temporary hack to unblock GCP migration.
    value = {
        'bugzilla': os.getenv('BUGZILLA_URL'),
        'phabricator': os.getenv('PHABRICATOR_URL'),
    }[service_name]
    if value:
        return value

    # Returns the corresponding service instance url based on the lando-api
    # url given. Errors out if given an invalid lando_api_url or service name.
    lando_api_hostname = urlparse(lando_api_url).netloc.split(':')[0].lower()
    return {
        'lando-api': {
            'bugzilla': 'http://bmo.test',
            'phabricator': 'http://phabricator.test'
        },
        'lando-api.test': {
            'bugzilla': 'http://bmo.test',
            'phabricator': 'http://phabricator.test'
        },
        'api.lando.devsvcdev.mozaws.net': {
            'bugzilla': 'https://bugzilla-dev.allizom.org',
            'phabricator': 'https://phabricator-dev.allizom.org'
        },
        'api.lando.services.mozilla.com': {
            'bugzilla': 'https://bugzilla.mozilla.org',
            'phabricator': 'https://phabricator.services.mozilla.com'
        }
    }[lando_api_hostname][service_name]
