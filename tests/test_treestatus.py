# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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


def test_update_form_validate_trees():
    pass


def test_update_form_validate_reason():
    pass


def test_update_form_validate_reason_category():
    pass


def test_update_form_to_submitted_json():
    pass


def test_recent_changes_action():
    pass
