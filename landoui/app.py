# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os

import click

from flask import Flask
from flask_assets import Environment
from flask_talisman import Talisman
from webassets.loaders import YAMLLoader

from landoui import auth

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
        'default-src':
        '\'self\'',
        # The following settings needed for Google Fonts from Semantic UI
        'font-src':
        '\'self\' themes.googleusercontent.com *.gstatic.com',
        'style-src':
        '\'self\' ajax.googleapis.com fonts.googleapis.com *.gstatic.com',
    }

    app = Flask(__name__)
    Talisman(app, content_security_policy=csp, force_https=use_https)

    # Set configuration
    app.config['VERSION_PATH'] = version_path
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
    from landoui.dockerflow import dockerflow
    app.register_blueprint(pages)
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
