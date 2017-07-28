# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import os
import logging

import click
from flask import Flask
from flask_assets import Environment
from flask_talisman import Talisman
from webassets.loaders import YAMLLoader

from landoui import auth
from landoui.logging import initialize_logging, log_config_change
from landoui.sentry import initialize_sentry

logger = logging.getLogger(__name__)

# This global is required to allow OIDC initialization on the entire app,
# yet still allow @oidc decorate uses for pages
oidc = None


def create_app(
    version_path, secret_key, session_cookie_name, session_cookie_domain,
    session_cookie_secure, use_https, enable_asset_pipeline
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

    # Set configuration
    app.config['VERSION_PATH'] = version_path
    log_config_change('VERSION_PATH', version_path)

    version_info = json.load(open(version_path))
    logger.info(version_info, 'app.version')

    this_app_version = version_info['version']
    initialize_sentry(app, this_app_version)

    # Set remaining configuration
    app.config['SECRET_KEY'] = secret_key
    app.config['SESSION_COOKIE_NAME'] = session_cookie_name
    app.config['SESSION_COOKIE_DOMAIN'] = session_cookie_domain
    app.config['SESSION_COOKIE_SECURE'] = session_cookie_secure
    app.config['SERVER_NAME'] = session_cookie_domain
    app.config['USE_HTTPS'] = use_https
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
def run_dev_server(
    debug, host, port, version_path, secret_key, session_cookie_name,
    session_cookie_domain, session_cookie_secure, use_https,
    enable_asset_pipeline
):
    """
    Run the development server which auto reloads when things change.
    """
    app = create_app(
        version_path, secret_key, session_cookie_name, session_cookie_domain,
        session_cookie_secure, use_https, enable_asset_pipeline
    )
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=debug, port=port, host=host)
