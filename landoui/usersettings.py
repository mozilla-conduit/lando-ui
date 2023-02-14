# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import (
    current_app,
    jsonify,
    Response,
)

from landoui.forms import UserSettingsForm


def manage_phab_api_token_cookie(form: UserSettingsForm, payload: dict) -> Response:
    """Sets `phabricator-api-token` cookie from the UserSettingsForm.

    Sets the cookie to the value provided in `phab_api_token` field.
    If `reset_phab_api_token` is `True` cookie is set to an empty string.

    Args:
        form: validated `landoui.forms.UserSettingsForm`

    Returns:
        `flask.Response` with a `Set-Cookie` header
    """
    payload["phab_api_token_set"] = (
        form.phab_api_token.data and not form.reset_phab_api_token.data
    )
    response = jsonify(payload)

    if form.reset_phab_api_token.data:
        response.delete_cookie("phabricator-api-token")
    elif form.phab_api_token.data:
        response.set_cookie(
            "phabricator-api-token",
            value=form.phab_api_token.data,
            secure=current_app.config["USE_HTTPS"],
            httponly=True,
        )

    return response
