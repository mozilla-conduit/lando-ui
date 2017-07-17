# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import os

import click
import logging

from flask import Flask
from flask_assets import Environment
from flask_talisman import Talisman
from mozlogging import MozLogFormatter
from webassets.loaders import YAMLLoader

from landoui import auth

logger = logging.getLogger(__name__)

# This global is required to allow OIDC initialization on the entire app,
# yet still allow @oidc decorate uses for pages
oidc = None


def create_app(
    version_path, secret_key, session_cookie_name, session_cookie_domain,
    session_cookie_secure, use_https
):
    """
    Create an app instance.
    """
    csp = {
        'default-src': "'self'",
        'font-src': "'self' https://code.cdn.mozilla.net",
        'style-src': "'self' https://code.cdn.mozilla.net",
        'img-src': "'self' *.cloudfront.net *.gravatar.com *.googleusercontent.com",
    } # yapf: disable

    initialize_logging()

    app = Flask(__name__)
    Talisman(app, content_security_policy=csp, force_https=use_https)

    # Set configuration
    app.config['VERSION_PATH'] = version_path
    version_info = json.load(open(version_path))
    logger.info(version_info, 'app.version')

    app.config['SECRET_KEY'] = secret_key
    app.config['SESSION_COOKIE_NAME'] = session_cookie_name
    app.config['SESSION_COOKIE_DOMAIN'] = session_cookie_domain
    app.config['SESSION_COOKIE_SECURE'] = session_cookie_secure
    app.config['SERVER_NAME'] = session_cookie_domain
    app.config['USE_HTTPS'] = use_https

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

    # Setup Flask Assets
    assets = Environment(app)
    loader = YAMLLoader(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'assets_src/assets.yml'
        )
    )
    assets.register(loader.load_bundles())

    return app


def initialize_logging():
    """Initialize application-wide logging."""
    mozlog_handler = logging.StreamHandler()
    mozlog_handler.setFormatter(MozLogFormatter())

    # We need to configure the logger just for our application code.  This is
    # because the MozLogFormatter changes the signature of the standard
    # library logging functions.  Any code that tries to log a message assuming
    # the standard library's formatter is in place, such as the code in the
    # libraries we use, with throw an error if the MozLogFormatter tries to
    # handle the message.
    app_logger = logging.getLogger('landoui')

    # Stop our specially-formatted log messages from bubbling up to any
    # Flask-installed loggers that may be present.  They will throw an exception
    # if they handle our messages.
    app_logger.propagate = False

    app_logger.addHandler(mozlog_handler)

    level = os.environ.get('LOG_LEVEL', 'INFO')
    app_logger.setLevel(level)

    log_config_change('LOG_LEVEL', level)


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
def run_dev_server(
    debug, host, port, version_path, secret_key, session_cookie_name,
    session_cookie_domain, session_cookie_secure, use_https
):
    """
    Run the development server which auto reloads when things change.
    """
    app = create_app(
        version_path, secret_key, session_cookie_name, session_cookie_domain,
        session_cookie_secure, use_https
    )
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=debug, port=port, host=host)


def log_config_change(setting_name, value):
    """Helper to log configuration changes.

    Args:
        setting_name: The setting being changed.
        value: The setting's new value.
    """
    logger.info({'setting': setting_name, 'value': value}, 'app.configure')
