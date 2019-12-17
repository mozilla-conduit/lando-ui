# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Blueprint for handling the sec-approval workflow.

See https://wiki.mozilla.org/Security/Bug_Approval_Process
"""

import logging

from flask import abort, Blueprint, current_app, flash, redirect, \
    render_template, session, url_for

from landoui.app import oidc
from landoui.forms import SecApprovalRequestForm
from landoui.helpers import (
    get_phabricator_api_token,
    set_last_local_referrer,
)
from landoui.landoapi import LandoAPI

logger = logging.getLogger(__name__)

secapproval = Blueprint("secapproval", __name__, url_prefix="/sec-approval")
secapproval.before_request(set_last_local_referrer)


@secapproval.route("/D<int:revision_id>/", methods=("GET", "POST"))
@oidc.oidc_auth
def create(revision_id):
    """Render and submit a sec-approval request for a revision."""
    if not current_app.config.get("ENABLE_SEC_APPROVAL"):
        abort(404)

    form = SecApprovalRequestForm()
    api_token = get_phabricator_api_token()

    if not api_token:
        flash(
            "Lando needs your Phabricator API token to post sec-approval "
            "requests and comments on your behalf. Please click on your "
            "username in the navigation bar above and fill in your "
            "Phabricator API key.", "warning"
        )

    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=api_token,
    )

    rname = "D{}".format(revision_id)
    stack = api.request("GET", "stacks/{}".format(rname))
    revision = next(r for r in stack["revisions"] if r["id"] == rname)

    if form.validate_on_submit() and api_token:
        logger.info(
            "sec-approval requested", extra={"revision_id": revision_id}
        )

        payload = {
            "revision_id": rname,
            "form_content":
            render_sec_approval_request_comment(form, revision_id),
        }

        if form.new_title.data:
            sanitized_message = "{}\n\n{}".format(
                form.new_title.data, form.new_summary.data
            ).strip()
            payload["sanitized_message"] = sanitized_message

        api.request(
            "POST",
            "requestSecApproval",
            require_auth0=True,
            json=payload,
        )

        flash("Your request for security review was successful.")
        return redirect(url_for('revisions.revision', revision_id=revision_id))

    status = 400 if form.errors else 200

    return (
        render_template(
            "secapproval/secapproval.html",
            form=form,
            revision_id=revision_id,
            commit_message=revision["commit_message"],
            commit_message_title=revision["title"],
            commit_message_summary=revision["summary"],
        ), status,
    )


def render_sec_approval_request_comment(
    form: SecApprovalRequestForm, revision_id: int
) -> str:
    """Render a Phabricator ReMarkup comment holding the user's answers to
    the sec-approval request form questions.
    """
    return render_template("secapproval/comment.html", form=form)
