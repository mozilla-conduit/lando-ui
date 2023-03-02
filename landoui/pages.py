# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import os

from typing import (
    Optional,
)

from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    redirect,
    render_template,
    session,
)

from landoui.app import oidc
from landoui.errorhandlers import UIError
from landoui.forms import UserSettingsForm
from landoui.helpers import set_last_local_referrer, is_user_authenticated
from landoui.usersettings import manage_phab_api_token_cookie

logger = logging.getLogger(__name__)

pages = Blueprint("page", __name__)
pages.before_request(set_last_local_referrer)


@pages.route("/")
def home():
    enable_transplant_ui = current_app.config.get("ENABLE_EMBEDDED_TRANSPLANT_UI")
    if not (enable_transplant_ui and is_user_authenticated()):
        # Return a static HTML page for users that are not logged in.
        return render_template("home.html")

    # Render the landing queue.
    return render_template("queue/queue.html")


@pages.route("/signin")
@oidc.oidc_auth("AUTH0")
def signin():
    redirect_url = session.get("last_local_referrer") or "/"
    return redirect(redirect_url)


@pages.route("/signout")
def signout():
    return render_template("signout.html")


@pages.route("/logout")
@oidc.oidc_logout
def logout():
    protocol = "https" if current_app.config["USE_HTTPS"] else "http"

    return_url = "{protocol}://{host}/signout".format(
        protocol=protocol, host=current_app.config["SERVER_NAME"]
    )

    logout_url = (
        "https://{auth0_host}/v2/logout?returnTo={return_url}&"
        "client_id={client_id}".format(
            auth0_host=os.environ["OIDC_DOMAIN"],
            return_url=return_url,
            client_id=os.environ["OIDC_CLIENT_ID"],
        )
    )

    response = make_response(redirect(logout_url, code=302))
    response.delete_cookie("phabricator-api-token")
    return response


@pages.route("/settings", methods=["POST"])
@oidc.oidc_auth("AUTH0")
def settings():
    if not is_user_authenticated():
        # Accessing it unauthenticated from UI is protected by CSP
        return jsonify(
            dict(success=False, errors=dict(form_errors=["User is not authenticated"]))
        )

    form = UserSettingsForm()
    if not form.validate_on_submit():
        return jsonify(dict(success=False, errors=form.errors))

    payload = dict(success=True)
    response = manage_phab_api_token_cookie(form, payload)
    return response


@oidc.error_view
def oidc_error(error: Optional[str] = None, error_description: Optional[str] = None):
    """Handles authentication errors returned by Auth0.

    When something goes wrong with authentication, Auth0 redirects to our
    provided redirect uri (simply /redirect_uri when using flask_pyoidc) with
    the above two query parameters: error and error_description.
    We hook into this using the @oidc.error_view decorator so we can handle
    recoverable errors.

    The most common error is with refreshing the user's session automatically,
    officially called "Silent Authentication" (see
    https://auth0.com/docs/api-auth/tutorials/silent-authentication).

    With silent authentication enabled, flask_pyoidc passes 'prompt=none'
    when it requests authentication. If the user's greater Single Sign On
    session is still active, then the user is logged in seamlessly and their
    lando-ui session is refreshed. When the user's greater Single Sign On
    session is expired, Auth0 explicitly raises a 'login_required' error and
    provides that at our redirect_uri. Auth0 requires that the login is
    requested _without_ the 'prompt=none' option. By clearing the current
    session, flask_pyoidc knows to request login with a prompt.

    In general, when something goes wrong, we logout the user so that they can
    try again from a fresh state. If the user wasn't logged in to begin with,
    then we display an error message and log it.
    """
    if is_user_authenticated() or error in ("login_required", "interaction_required"):
        # last_local_referrer is guaranteed to not be a signin/signout route.
        redirect_url = session.get("last_local_referrer") or "/"
        session.clear()
        response = make_response(redirect(redirect_url))
        response.delete_cookie("phabricator-api-token")
        return response
    else:
        logger.error(
            "authentication error",
            extra={"error": error, "error_description": error_description},
        )  # yapf: disable
        raise UIError(
            title="Authentication Error: {}".format(error), message=error_description
        )
