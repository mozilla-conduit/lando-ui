# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os

from flask import (
    Blueprint, current_app, jsonify, redirect, render_template, session
)

from landoui.app import oidc

pages = Blueprint('page', __name__)


def is_logged_in():
    # TODO:  There surely must be a better/more secure way to establish
    # if the user is logged in or not.  Maybe from oidc?
    return 'id_token' in session


@pages.route('/info')
@oidc.oidc_auth
def info():
    """Return the JSONified user session for debugging."""
    return jsonify(
        id_token=session['id_token'],
        access_token=session['access_token'],
        userinfo=session['userinfo']
    )


@pages.route('/')
def home():
    return render_template('home.html', logged_in=is_logged_in())


@pages.route('/protected')
@oidc.oidc_auth
def protected():
    return render_template('protected.html')


@pages.route('/signout')
def signout():
    return render_template('signout.html')


@pages.route('/logout')
@oidc.oidc_logout
def logout():
    protocol = 'https' if current_app.config['USE_HTTPS'] else 'http'

    return_url = '{protocol}://{host}/signout'.format(
        protocol=protocol, host=current_app.config['SERVER_NAME']
    )

    logout_url = 'https://{auth0_host}/v2/logout?returnTo={return_url}&client_id={client_id}'.format(
        auth0_host=os.environ['OIDC_DOMAIN'],
        return_url=return_url,
        client_id=os.environ['OIDC_CLIENT_ID']
    )

    return redirect(logout_url, code=302)
