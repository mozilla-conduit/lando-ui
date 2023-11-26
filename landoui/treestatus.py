# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import (
    Optional,
)

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from landoui.helpers import (
    set_last_local_referrer,
)
from landoui.landoapi import (
    LandoAPI,
    LandoAPIError,
)
from landoui.forms import (
    ReasonCategory,
    TreeCategory,
    TreeStatusLogUpdateForm,
    TreeStatusNewTreeForm,
    TreeStatusRecentChangesForm,
    TreeStatusUpdateTreesForm,
)

treestatus_blueprint = Blueprint("treestatus", __name__)
treestatus_blueprint.before_request(set_last_local_referrer)


def get_recent_changes_stack(api: LandoAPI) -> list[dict]:
    """Retrieve recent changes stack data with error handling."""
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

    return response["result"]


def build_recent_changes_stack(
    recent_changes_data: list[dict],
) -> list[tuple[TreeStatusRecentChangesForm, dict]]:
    """Build the recent changes stack object."""
    return [
        (
            TreeStatusRecentChangesForm(
                id=change["id"],
                reason=change["reason"],
                reason_category=(
                    change["trees"][0]["last_state"]["current_tags"][0]
                    if change["trees"][0]["last_state"]["current_tags"]
                    else ReasonCategory.NO_CATEGORY.value
                ),
            ),
            change,
        )
        for change in recent_changes_data
    ]


@treestatus_blueprint.route("/treestatus/", methods=["GET", "POST"])
def treestatus():
    """Display the status of all the current trees.

    This view is the main landing page for Treestatus. The view is a list of all trees
    and their current statuses. The view of all trees is a form where each tree can be
    selected, and "Update trees" passes the selection along to the tree updating form.
    """
    api = LandoAPI.from_environment()

    treestatus_update_trees_form = TreeStatusUpdateTreesForm()
    if treestatus_update_trees_form.validate_on_submit():
        # Submit the form.
        return update_treestatus(api, treestatus_update_trees_form)

    if (
        treestatus_update_trees_form.is_submitted()
        and not treestatus_update_trees_form.validate()
    ):
        # Flash form submission errors.
        for errors in treestatus_update_trees_form.errors.values():
            for error in errors:
                flash(error, "warning")

    trees_response = api.request("GET", "treestatus/trees")
    trees = trees_response.get("result")

    if not treestatus_update_trees_form.trees.entries:
        ordered_tree_choices = sorted(trees.values(), key=TreeCategory.sort_trees)
        for tree in ordered_tree_choices:
            treestatus_update_trees_form.trees.append_entry(tree["tree"])

    recent_changes_data = get_recent_changes_stack(api)
    recent_changes_stack = build_recent_changes_stack(recent_changes_data)

    return render_template(
        "treestatus/trees.html",
        recent_changes_stack=recent_changes_stack,
        trees=trees,
        treestatus_update_trees_form=treestatus_update_trees_form,
    )


def update_treestatus(api: LandoAPI, update_trees_form: TreeStatusUpdateTreesForm):
    """Handler for the tree status updating form.

    This function handles form submission for the status updating form. Validate
    the form submission and submit a request to LandoAPI, redirecting to the main
    Treestatus page on success. Display an error message and return to the form if
    the status updating rules were broken or the API returned an error.
    """
    try:
        api.request(
            "PATCH",
            "treestatus/trees",
            require_auth0=True,
            json=update_trees_form.to_submitted_json(),
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        flash(f"Could not update trees: {exc.detail}. Please try again later.", "error")
        return redirect(request.referrer), 303

    # Redirect to the main Treestatus page.
    flash("Tree statuses updated successfully.")
    return redirect(url_for("treestatus.treestatus"))


@treestatus_blueprint.route("/treestatus/new_tree/", methods=["GET", "POST"])
def new_tree():
    """View for the new tree form."""
    api = LandoAPI.from_environment()
    treestatus_new_tree_form = TreeStatusNewTreeForm()

    if treestatus_new_tree_form.validate_on_submit():
        return new_tree_handler(api, treestatus_new_tree_form)

    recent_changes_data = get_recent_changes_stack(api)
    recent_changes_stack = build_recent_changes_stack(recent_changes_data)

    return render_template(
        "treestatus/new_tree.html",
        treestatus_new_tree_form=treestatus_new_tree_form,
        recent_changes_stack=recent_changes_stack,
    )


def new_tree_handler(api: LandoAPI, form: TreeStatusNewTreeForm):
    """Handler for the new tree form."""
    # Retrieve data from the form.
    tree = form.tree.data
    tree_category = form.category.data

    try:
        api.request(
            "PUT",
            f"treestatus/trees/{tree}",
            require_auth0=True,
            json={
                "tree": tree,
                "category": tree_category,
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
        return redirect(request.referrer), 303

    flash(f"New tree {tree} created successfully.")
    return redirect(url_for("treestatus.treestatus"))


@treestatus_blueprint.route("/treestatus/<tree>/", methods=["GET"])
def treestatus_tree(tree: str):
    """Display the log of statuses for an individual tree."""
    api = LandoAPI.from_environment()

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

    recent_changes_data = get_recent_changes_stack(api)
    recent_changes_stack = build_recent_changes_stack(recent_changes_data)

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

    if reason_category and ReasonCategory.is_valid_for_backend(reason_category):
        json_body["tags"] = [reason_category]

    return json_body


@treestatus_blueprint.route("/treestatus/stack/<int:id>", methods=["POST"])
def update_change(id: int):
    """Handler for stack updates.

    This function handles form submissions for updates to entries in the recent changes
    stack. This includes pressing the "restore" or "discard" buttons, as well as updates
    to the reason and reason category after pressing "edit" and "update".
    """
    api = LandoAPI.from_environment()
    recent_changes_form = TreeStatusRecentChangesForm()

    restore = recent_changes_form.restore.data
    update = recent_changes_form.update.data
    discard = recent_changes_form.discard.data

    if restore:
        # Restore is a DELETE with a status revert.
        method = "DELETE"
        request_args = {"params": {"revert": 1}}

        flash_message = "Status change restored."
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
            require_auth0=True,
            **request_args,
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        flash(
            f"Could not modify recent change: {exc.detail}. Please try again later.",
            "error",
        )
        return redirect(request.referrer), 303

    flash(flash_message)
    return redirect(request.referrer)


@treestatus_blueprint.route("/treestatus/log/<int:id>", methods=["POST"])
def update_log(id: int):
    """Handler for log updates.

    This function handles form submissions for updates to individual log entries
    in the per-tree log view.
    """
    api = LandoAPI.from_environment()

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
        return redirect(request.referrer), 303

    flash("Log entry updated.")
    return redirect(request.referrer)
