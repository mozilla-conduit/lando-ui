# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import (
    Optional,
)

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from landoui.helpers import (
    get_phabricator_api_token,
    set_last_local_referrer,
)
from landoui.landoapi import (
    LandoAPI,
    LandoAPIError,
)
from landoui.forms import (
    ReasonCategory,
    TreeStatusLogUpdateForm,
    TreeStatusNewTreeForm,
    TreeStatusRecentChangesForm,
    TreeStatusSelectTreesForm,
    TreeStatusUpdateTreesForm,
)

treestatus_blueprint = Blueprint("treestatus", __name__)
treestatus_blueprint.before_request(set_last_local_referrer)


def build_recent_changes_stack(
    api: LandoAPI,
) -> list[tuple[TreeStatusRecentChangesForm, dict]]:
    """Build the recent changes stack object."""
    try:
        response = api.request(
            "GET",
            "treestatus/stack",
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        flash(f"Could not retrieve recent changes stack: {exc.detail}.", "error")
        return []

    return [
        (
            TreeStatusRecentChangesForm(
                id=change["id"],
                reason=change["reason"],
                reason_category=change["trees"][0]["last_state"]["current_tags"][0],
                who=change["who"],
                when=change["when"],
            ),
            change,
        )
        for change in response["result"]
    ]


@treestatus_blueprint.route("/treestatus/", methods=["GET"])
def treestatus():
    """Display the status of all the current trees."""
    token = get_phabricator_api_token()
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )

    treestatus_select_trees_form = TreeStatusSelectTreesForm()

    trees_response = api.request("GET", "treestatus/trees")
    trees = trees_response.get("result")

    for tree in trees:
        treestatus_select_trees_form.trees.append_entry(tree)

    recent_changes_stack = build_recent_changes_stack(api)

    return render_template(
        "treestatus/trees.html",
        recent_changes_stack=recent_changes_stack,
        trees=trees,
        treestatus_select_trees_form=treestatus_select_trees_form,
    )


@treestatus_blueprint.route("/treestatus/update", methods=["POST"])
def update_treestatus_form():
    """Web UI for the tree status updating form."""
    token = get_phabricator_api_token()
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )

    treestatus_select_trees_form = TreeStatusSelectTreesForm()
    if not treestatus_select_trees_form.validate_on_submit():
        # Validate the tree selection form was submitted with at least one
        # tree selected.
        for errors in treestatus_select_trees_form.errors.values():
            for error in errors:
                flash(error, "warning")

        return redirect(request.referrer)

    treestatus_update_trees_form = TreeStatusUpdateTreesForm()

    recent_changes_stack = build_recent_changes_stack(api)

    return render_template(
        "treestatus/update_trees.html",
        recent_changes_stack=recent_changes_stack,
        treestatus_update_trees_form=treestatus_update_trees_form,
    )


@treestatus_blueprint.route("/treestatus/update_handler", methods=["POST"])
def update_treestatus():
    """Handler for the tree status updating form."""
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=get_phabricator_api_token(),
    )
    treestatus_update_trees_form = TreeStatusUpdateTreesForm()

    if not treestatus_update_trees_form.validate_on_submit():
        for errors in treestatus_update_trees_form.errors.values():
            for error in errors:
                flash(error, "warning")

        # Return the result of re-rendering the form, so the current state of
        # the form is preserved.
        return update_treestatus_form()

    # Retrieve data from the form.
    trees = treestatus_update_trees_form.trees.data
    status = treestatus_update_trees_form.status.data
    reason = treestatus_update_trees_form.reason.data
    message_of_the_day = treestatus_update_trees_form.message_of_the_day.data
    reason_category = treestatus_update_trees_form.reason_category.data
    remember = treestatus_update_trees_form.remember_this_change.data

    try:
        api.request(
            "PATCH",
            "treestatus/trees",
            # TODO re-add auth0 requirement.
            # require_auth0=True,
            json={
                "trees": trees,
                "status": status,
                "reason": reason,
                "message_of_the_day": message_of_the_day,
                "tags": [reason_category],
                "remember": remember,
            },
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        flash(f"Could not update trees: {exc.detail}. Please try again later.", "error")
        return redirect(request.referrer), 500

    # Redirect to the main Treestatus page.
    flash("Tree statuses updated successfully.")
    return redirect(url_for("treestatus.treestatus"))


@treestatus_blueprint.route("/treestatus/new_tree/", methods=["GET", "POST"])
def new_tree():
    """View for the new tree form."""
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=get_phabricator_api_token(),
    )
    treestatus_new_tree_form = TreeStatusNewTreeForm()

    if treestatus_new_tree_form.validate_on_submit():
        return new_tree_handler(api, treestatus_new_tree_form)

    recent_changes_stack = build_recent_changes_stack(api)

    return render_template(
        "treestatus/new_tree.html",
        treestatus_new_tree_form=treestatus_new_tree_form,
        recent_changes_stack=recent_changes_stack,
    )


def new_tree_handler(api: LandoAPI, form: TreeStatusNewTreeForm):
    """Handler for the new tree form."""
    # Retrieve data from the form.
    tree = form.tree.data

    try:
        api.request(
            "PUT",
            f"treestatus/trees/{tree}",
            # TODO re-enable auth0 requirement.
            # require_auth0=True,
            json={
                "tree": tree,
                # Trees are open on creation.
                "status": "open",
                "reason": "",
                "message_of_the_day": "",
            },
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        flash(
            f"Could not create new tree: {exc.detail}. Please try again later.", "error"
        )
        return redirect(request.referrer), 500

    flash(f"New tree {tree} created successfully.")
    return redirect(url_for("treestatus.treestatus"))


@treestatus_blueprint.route("/treestatus/<tree>/", methods=["GET"])
def treestatus_tree(tree: str):
    """Display the log of statuses for a given tree."""
    token = get_phabricator_api_token()
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )

    logs_response = api.request("GET", f"treestatus/trees/{tree}/logs")
    logs = logs_response.get("result")
    if not logs:
        flash(
            f"Could not retrieve status logs for {tree} from Lando, try again later.",
            "error",
        )
        return redirect(request.referrer)

    current_log = logs[0]

    logs = [
        (
            TreeStatusLogUpdateForm(
                reason=log["reason"],
                reason_category=log["tags"][0]
                if log["tags"]
                else ReasonCategory.NO_CATEGORY.value,
            ),
            log,
        )
        for log in logs
    ]

    recent_changes_stack = build_recent_changes_stack(api)

    return render_template(
        "treestatus/log.html",
        current_log=current_log,
        logs=logs,
        recent_changes_stack=recent_changes_stack,
        tree=tree,
    )


def build_update_json_body(
    reason: Optional[str], reason_category: Optional[str]
) -> dict:
    """Return a `dict` for use as a JSON body in a log/change update."""
    json_body = {}

    json_body["reason"] = reason

    if reason_category and ReasonCategory.is_valid_reason_category(reason_category):
        json_body["tags"] = [reason_category]

    return json_body


@treestatus_blueprint.route("/treestatus/stack/<int:id>", methods=["POST"])
def update_change(id: int):
    """Handler for stack updates."""
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=get_phabricator_api_token(),
    )
    recent_changes_form = TreeStatusRecentChangesForm()

    restore = recent_changes_form.restore.data
    update = recent_changes_form.update.data
    discard = recent_changes_form.discard.data

    if restore:
        # Restore is a DELETE with a status revert.
        method = "DELETE"
        request_args = {"params": {"revert": 1}}

        flash_message = "Statuses change restored."
    elif discard:
        # Discard is a DELETE without a status revert.
        method = "DELETE"
        request_args = {"params": {"revert": 0}}

        flash_message = "Status change discarded."
    elif update:
        # Update is a PATCH with any changed attributes passed in the body.
        method = "PATCH"

        reason = recent_changes_form.reason.data
        reason_category = recent_changes_form.reason_category.data

        request_args = {"json": build_update_json_body(reason, reason_category)}

        flash_message = "Status change updated."
    else:
        # This should not happen, but just in case.
        flash("Invalid submit input on change update form.", "error")
        return redirect(request.referrer)

    try:
        api.request(
            method,
            f"treestatus/stack/{id}",
            # TODO re-enable auth0 requirement.
            # require_auth0=True,
            **request_args,
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        flash(
            f"Could not modify recent change: {exc.detail}. Please try again later.",
            "error",
        )
        return redirect(request.referrer), 500

    flash(flash_message)
    return redirect(request.referrer)


@treestatus_blueprint.route("/treestatus/log/<int:id>", methods=["POST"])
def update_log(id: int):
    """Handler for log updates."""
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=get_phabricator_api_token(),
    )

    log_update_form = TreeStatusLogUpdateForm()

    reason = log_update_form.reason.data
    reason_category = log_update_form.reason_category.data

    json_body = build_update_json_body(reason, reason_category)

    try:
        api.request(
            "PATCH",
            f"treestatus/log/{id}",
            json=json_body,
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        flash(
            f"Could not modify log entry: {exc.detail}. Please try again later.",
            "error",
        )
        return redirect(request.referrer), 500

    flash("Log entry updated.")
    return redirect(request.referrer)
