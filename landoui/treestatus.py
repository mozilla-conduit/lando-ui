# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

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
    TreestatusAPI,
    LandoAPIError,
)
from landoui.forms import (
    ReasonCategory,
    TreeCategory,
    TreeStatusLogUpdateForm,
    TreeStatusNewTreeForm,
    TreeStatusRecentChangesForm,
    TreeStatusUpdateTreesForm,
    build_update_json_body,
)

logger = logging.getLogger(__name__)

treestatus_blueprint = Blueprint("treestatus", __name__)
treestatus_blueprint.before_request(set_last_local_referrer)


def get_recent_changes_stack(api: TreestatusAPI) -> list[dict]:
    """Retrieve recent changes stack data with error handling."""
    try:
        response = api.request(
            "GET",
            "stack",
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
    selected, and clicking "Update trees" opens a modal which presents the tree updating
    form.
    """
    api = TreestatusAPI.from_environment()

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

    trees_response = api.request("GET", "trees")
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


def update_treestatus(api: TreestatusAPI, update_trees_form: TreeStatusUpdateTreesForm):
    """Handler for the tree status updating form.

    This function handles form submission for the status updating form. Validate
    the form submission and submit a request to LandoAPI, redirecting to the main
    Treestatus page on success. Display an error message and return to the form if
    the status updating rules were broken or the API returned an error.
    """
    logger.info(f"Requesting tree status update.")

    try:
        api.request(
            "PATCH",
            "trees",
            require_auth0=True,
            json=update_trees_form.to_submitted_json(),
        )
    except LandoAPIError as exc:
        logger.exception("Request to update trees status failed.")
        if not exc.detail:
            raise exc

        flash(f"Could not update trees: {exc.detail}. Please try again later.", "error")
        return redirect(request.referrer), 303

    # Redirect to the main Treestatus page.
    logger.info("Tree statuses updated successfully.")
    flash("Tree statuses updated successfully.")
    return redirect(url_for("treestatus.treestatus"))


@treestatus_blueprint.route("/treestatus/new_tree/", methods=["GET", "POST"])
def new_tree():
    """View for the new tree form."""
    api = TreestatusAPI.from_environment()
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


def new_tree_handler(api: TreestatusAPI, form: TreeStatusNewTreeForm):
    """Handler for the new tree form."""
    # Retrieve data from the form.
    tree = form.tree.data
    tree_category = form.category.data

    logger.info(f"Requesting new tree {tree}.")

    try:
        api.request(
            "PUT",
            f"trees/{tree}",
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
        logger.exception(f"Could not create new tree {tree}.")

        if not exc.detail:
            raise exc

        flash(
            f"Could not create new tree: {exc.detail}. Please try again later.", "error"
        )
        return redirect(request.referrer), 303

    logger.info(f"New tree {tree} created successfully.")
    flash(f"New tree {tree} created successfully.")
    return redirect(url_for("treestatus.treestatus"))


@treestatus_blueprint.route("/treestatus/<tree>/", methods=["GET"])
def treestatus_tree(tree: str):
    """Display the log of statuses for an individual tree."""
    api = TreestatusAPI.from_environment()

    try:
        logs_response = api.request("GET", f"trees/{tree}/logs")

        # We got a response, if this is empty is it an error.
        logs = logs_response.get("result")
        detail = "empty response from Lando"
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        # We got some exception back from LandoAPI..
        detail = exc.detail
        logs = []

    if not logs:
        error = (f"Could not retrieve status logs for {tree}: {detail}.",)
        logger.error(error)
        flash(error, "error")
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


@treestatus_blueprint.route("/treestatus/stack/<int:id>", methods=["POST"])
def update_change(id: int):
    """Handler for stack updates.

    This function handles form submissions for updates to entries in the recent changes
    stack. This includes pressing the "restore" or "discard" buttons, as well as updates
    to the reason and reason category after pressing "edit" and "update".
    """
    api = TreestatusAPI.from_environment()
    recent_changes_form = TreeStatusRecentChangesForm()

    action = recent_changes_form.to_action()

    logger.info(f"Requesting stack update for stack id {id}.")

    try:
        api.request(
            action.method,
            f"stack/{id}",
            require_auth0=True,
            **action.request_args,
        )
    except LandoAPIError as exc:
        logger.exception(f"Stack entry {id} failed to update.")

        if not exc.detail:
            raise exc

        flash(
            f"Could not modify recent change: {exc.detail}. Please try again later.",
            "error",
        )
        return redirect(request.referrer), 303

    logger.info(f"Stack entry {id} updated.")
    flash(action.message)
    return redirect(request.referrer)


@treestatus_blueprint.route("/treestatus/log/<int:id>", methods=["POST"])
def update_log(id: int):
    """Handler for log updates.

    This function handles form submissions for updates to individual log entries
    in the per-tree log view.
    """
    api = TreestatusAPI.from_environment()

    log_update_form = TreeStatusLogUpdateForm()

    reason = log_update_form.reason.data
    reason_category = log_update_form.reason_category.data

    json_body = build_update_json_body(reason, reason_category)

    logger.info(f"Requesting log update for log id {id}.")

    try:
        api.request(
            "PATCH",
            f"log/{id}",
            require_auth0=True,
            json=json_body,
        )
    except LandoAPIError as exc:
        logger.exception(f"Log entry {id} failed to update.")

        if not exc.detail:
            raise exc

        flash(
            f"Could not modify log entry: {exc.detail}. Please try again later.",
            "error",
        )
        return redirect(request.referrer), 303

    logger.info(f"Log entry {id} updated.")
    flash("Log entry updated.")
    return redirect(request.referrer)
