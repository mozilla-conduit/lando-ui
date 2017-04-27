# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import click

from flask import Flask


@click.command()
@click.option(
    '--run-dev-server', envvar='RUN_DEV_SERVER', type=bool, default=False
)
@click.option('--debug', envvar='DEBUG', type=bool, default=False)
@click.option('--port', envvar='PORT', type=int, default=80)
@click.option('--host', envvar='HOST', default='0.0.0.0')
@click.option('--secret-key', envvar='SECRET_KEY', default=None)
@click.option(
    '--session-cookie-name', envvar='SESSION_COOKIE_NAME', default=None
)
@click.option(
    '--session-cookie-domain', envvar="SESSION_COOKIE_DOMAIN", default=""
)
@click.option(
    '--session-cookie-secure', envvar='SESSION_COOKIE_SECURE', default=True
)
def create_app(
    run_dev_server, debug, port, host, secret_key, session_cookie_name,
    session_cookie_domain, session_cookie_secure
):
    app = Flask(__name__)

    # Set configuration
    app.config['SECRET_KEY'] = secret_key
    app.config['SESSION_COOKIE_NAME'] = session_cookie_name
    app.config['SESSION_COOKIE_DOMAIN'] = session_cookie_domain
    app.config['SESSION_COOKIE_SECURE'] = session_cookie_secure

    # Register routes via Flask Blueprints
    from landoui.dockerflow import dockerflow
    app.register_blueprint(dockerflow)

    if run_dev_server:
        app.run(debug=debug, port=port, host=host)

    return app
