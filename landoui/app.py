# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os

import click

from flask import Flask
from flask_assets import Environment
from webassets.loaders import YAMLLoader

from landoui import auth

# This global is required to allow OIDC initialization on the entire app,
# yet still allow @oidc decorate uses for pages
oidc = None


@click.command()
@click.option(
    '--run-dev-server', envvar='RUN_DEV_SERVER', type=bool, default=False
)
@click.option('--debug', envvar='DEBUG', type=bool, default=False)
@click.option('--port', envvar='PORT', type=int, default=80)
@click.option('--host', envvar='HOST', default='0.0.0.0')
@click.option(
    '--version-path', envvar='VERSION_PATH', default='/app/version.json'
)
@click.option('--secret-key', envvar='SECRET_KEY', default=None)
@click.option(
    '--session-cookie-name', envvar='SESSION_COOKIE_NAME', default=None
)
@click.option(
    '--session-cookie-domain',
    envvar='SESSION_COOKIE_DOMAIN',
    default='lando.mozilla.org'
)
@click.option(
    '--session-cookie-secure', envvar='SESSION_COOKIE_SECURE', default=1
)
@click.option('--use-https', envvar='USE_HTTPS', default=1)
def create_app(
    run_dev_server, debug, port, host, version_path, secret_key,
    session_cookie_name, session_cookie_domain, session_cookie_secure,
    use_https
):
    app = Flask(__name__)

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
            os.path.dirname(os.path.abspath(__file__)), 'static/src/assets.yml'
        )
    )
    assets.register(loader.load_bundles())

    if run_dev_server:
        app.jinja_env.auto_reload = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.run(debug=debug, port=port, host=host)

    return app
