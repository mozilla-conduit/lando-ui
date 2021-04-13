# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    session,
)

from landoui.forms import RepoNoticeForm
from landoui.helpers import (
    is_user_authenticated,
    set_last_local_referrer,
)
from landoui.landoapi import LandoAPI, LandoAPIError

logger = logging.getLogger(__name__)

repo_notices = Blueprint("repos_notices", __name__)
repo_notices.before_request(set_last_local_referrer)


@repo_notices.route("/repos/notices/", methods=("GET", "POST"))
@repo_notices.route("/repos/notices/<int:notice_id>", methods=("PUT", "DELETE"))
def manage_repo_notices(notice_id=None):
    if not is_user_authenticated():
        errors = {"Error": ["You must be logged in to update a landing job."]}
        return jsonify(errors=errors), 401

    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
    )

    if request.method == "GET":
        try:
            data = api.request("GET", "repos/notices", require_auth0=True,)
            return jsonify(data)
        except LandoAPIError as e:
            return e.response, e.response["status"]
    elif request.method == "POST":
        try:
            data = request.get_json()
            form = RepoNoticeForm(data=data)
            if not form.validate():
                return jsonify(dict(form.errors)), 400

            data = form.data.copy()
            if data.get("start_date"):
                data["start_date"] = data["start_date"].isoformat()

            if data.get("end_date"):
                data["end_date"] = data["end_date"].isoformat()

            response = api.request(
                "POST", "repos/notices", require_auth0=True, json=data,
            )
            return jsonify(response), 201
        except LandoAPIError as e:
            return e.response, e.response["status"]
    elif request.method == "PUT":
        raise NotImplementedError()
    elif request.method == "DELETE":
        try:
            response = api.request(
                "DELETE", f"repos/notices/{notice_id}", require_auth0=True
            )
            return jsonify(response), 200
        except LandoAPIError as e:
            return e.response, e.response["status"]
