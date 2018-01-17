# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import os

from flask import (
    Blueprint, current_app, jsonify, redirect, render_template, session
)

from landoui.app import oidc
from landoui.helpers import set_last_local_referrer

logger = logging.getLogger(__name__)

pages = Blueprint('page', __name__)
pages.before_request(set_last_local_referrer)


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
    return render_template('home.html')


@pages.route('/signin')
@oidc.oidc_auth
def signin():
    redirect_url = session.get('last_local_referrer') or '/'
    return redirect(redirect_url)


@pages.route('/protected')
@oidc.oidc_auth
def protected():
    logger.warn(
        {
            'user_name': session['userinfo']['name']
        }, 'ProtectedPageView'
    )
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

    logout_url = (
        'https://{auth0_host}/v2/logout?returnTo={return_url}&'
        'client_id={client_id}'.format(
            auth0_host=os.environ['OIDC_DOMAIN'],
            return_url=return_url,
            client_id=os.environ['OIDC_CLIENT_ID']
        )
    )

    return redirect(logout_url, code=302)
