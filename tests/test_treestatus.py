# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from wtforms.validators import ValidationError

from landoui.forms import (
    RecentChangesAction,
    TreeStatusRecentChangesForm,
    TreeStatusUpdateTreesForm,
)
from landoui.treestatus import (
    build_recent_changes_stack,
    build_update_json_body,
)


def test_build_recent_changes_stack(app):
    recent_changes_data = [
        {
            "id": None,
            "reason": "reason 2",
            "trees": [{"last_state": {"current_tags": ["category 1"]}}],
            "who": "user2",
            "when": "now",
        },
        {
            "id": 2,
            "reason": "reason 2",
            "trees": [{"last_state": {"current_tags": ["category 2"]}}],
            "who": "user2",
            "when": "now",
        },
        {
            "id": 3,
            "reason": "reason 3",
            "trees": [{"last_state": {"current_tags": []}}],
            "who": "user3",
            "when": "now",
        },
    ]

    recent_changes_stack = build_recent_changes_stack(recent_changes_data)

    for form, data in recent_changes_stack:
        assert form.id.data == data["id"]
        assert form.reason.data == data["reason"]

        if form.id.data == 3:
            assert (
                form.reason_category.data == ""
            ), "Empty tags should set field to an empty string."
        else:
            assert (
                form.reason_category.data
                == data["trees"][0]["last_state"]["current_tags"][0]
            )


def test_build_update_json_body():
    assert build_update_json_body(None, None) == {
        "reason": None,
    }

    assert build_update_json_body("blah", None) == {
        "reason": "blah",
    }

    assert build_update_json_body("blah", "") == {
        "reason": "blah",
    }, "`tags` should not be set for empty reason category."

    assert build_update_json_body("blah", "asdf") == {
        "reason": "blah",
    }, "`tags` should not be set for invalid reason category."

    assert build_update_json_body("blah", "backlog") == {
        "reason": "blah",
        "tags": ["backlog"],
    }, "`tags` should be set for valid reason category."


def test_update_form_validate_trees(app):
    form = TreeStatusUpdateTreesForm()

    # At least one tree is required.
    with pytest.raises(ValidationError):
        form.validate_trees(form.trees)

    form.trees.append_entry("autoland")
    assert (
        form.validate_trees(form.trees) is None
    ), "Form with a tree entry should be valid."


def test_update_form_validate_reason(app):
    form = TreeStatusUpdateTreesForm(
        status="open",
    )
    assert (
        form.validate_reason(form.reason) is None
    ), "No validation required for `open` status."

    form = TreeStatusUpdateTreesForm(
        status="approval required",
    )
    assert (
        form.validate_reason(form.reason) is None
    ), "No validation required for `approval required` status."

    # `closed` status requires a reason.
    form = TreeStatusUpdateTreesForm(
        status="closed",
    )
    with pytest.raises(ValidationError):
        form.validate_reason(form.reason)

    form = TreeStatusUpdateTreesForm(
        status="closed",
        reason="some reason",
    )
    assert (
        form.validate_reason(form.reason) is None
    ), "`closed` status with a reason is valid."


def test_update_form_validate_reason_category(app):
    form = TreeStatusUpdateTreesForm(
        status="open",
    )
    assert (
        form.validate_reason_category(form.reason_category) is None
    ), "No validation required for `open` status."

    form = TreeStatusUpdateTreesForm(
        status="approval required",
    )
    assert (
        form.validate_reason_category(form.reason_category) is None
    ), "No validation required for `approval required` status."

    # `closed` status requires a reason category.
    form = TreeStatusUpdateTreesForm(
        status="closed",
    )
    with pytest.raises(ValidationError):
        form.validate_reason_category(form.reason_category)

    # `closed` status requires a non-empty reason category.
    form = TreeStatusUpdateTreesForm(
        status="closed",
        reason_category="",
    )
    with pytest.raises(ValidationError):
        form.validate_reason_category(form.reason_category)

    # `closed` status requires a valid reason category.
    form = TreeStatusUpdateTreesForm(
        status="closed",
        reason_category="blah",
    )
    with pytest.raises(ValidationError):
        form.validate_reason_category(form.reason_category)

    form = TreeStatusUpdateTreesForm(
        status="closed",
        reason_category="backlog",
    )
    assert (
        form.validate_reason_category(form.reason_category) is None
    ), "`closed` status with valid reason category is valid."


def test_update_form_to_submitted_json(app):
    form = TreeStatusUpdateTreesForm(
        status="open",
        reason="reason",
        message_of_the_day="",
        remember=True,
        reason_category="backlog",
    )

    form.trees.append_entry("autoland")
    form.trees.append_entry("mozilla-central")

    assert form.to_submitted_json() == {
        "status": "open",
        "reason": "reason",
        "message_of_the_day": "",
        "remember": True,
        "tags": ["backlog"],
        "trees": ["autoland", "mozilla-central"],
    }, "JSON format should match expected."


def test_recent_changes_action(app):
    form = TreeStatusRecentChangesForm(
        reason="reason",
        category="backlog",
    )

    form.update.data = True
    action = form.to_action()

    assert action.method == "PATCH", "Updates should use HTTP `PATCH`."
    assert "json" in action.request_args, "Updates should send content in JSON body."
    assert action.message == "Status change updated."

    form.update.data = False
    form.restore.data = True
    action = form.to_action()

    assert action.method == "DELETE", "Restores should use HTTP `DELETE`."
    assert (
        "params" in action.request_args
    ), "Restores should send content in query string."
    assert action.message == "Status change restored."

    form.restore.data = False
    form.discard.data = True
    action = form.to_action()

    assert action.method == "DELETE", "Discards should use HTTP `DELETE`."
    assert (
        "params" in action.request_args
    ), "Discards should send content in query string."
    assert action.message == "Status change discarded."
