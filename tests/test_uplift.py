# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from landoui.uplift import render_approval_comment

COMMON_COMMENT = """===== User impact if declined  =====

Not a lot of impact.

===== Steps to reproduce =====

Crash it, that&#39;s all.

===== Why is the change risky/not risky ? =====

Really risky

===== Is this code covered by automated tests ? =====

{icon check color=green} Yes


===== Has the fix been verified in Nightly ? =====

{icon times color=red} No


===== Risk to taking this patch =====

medium

===== Needs manual test from QE ? =====

{icon check color=green} Yes


===== String changes made/needed =====

None."""

VALID_UPLIFT_COMMENT = """



= Uplift request details =

View [source revision D1234](/D1234)

""" + COMMON_COMMENT

VALID_APPROVAL_COMMENT = """



= Approval request details =

""" + COMMON_COMMENT


def test_uplift_comment_rendering(app):
    """Test rendering the uplift form"""
    form = render_approval_comment(
        form_data={
            "user_impact": "Not a lot of impact.",
            "steps_to_reproduce": "Crash it, that's all.",
            "risky": "Really risky",
            "automated_tests": True,
            "nightly": False,
            "risk": "medium",
            "manual_qe": True,
            "string_changes": "None.",
            "bug_ids": ["1233"],
        },
        source_revision_id=1234,
    )
    assert form == VALID_UPLIFT_COMMENT


def test_approval_comment_rendering(app):
    """Test rendering the approval form"""
    form = render_approval_comment(
        form_data={
            "user_impact": "Not a lot of impact.",
            "steps_to_reproduce": "Crash it, that's all.",
            "risky": "Really risky",
            "automated_tests": True,
            "nightly": False,
            "risk": "medium",
            "manual_qe": True,
            "string_changes": "None.",
            "bug_ids": ["1233"],
        },
    )
    assert form == VALID_APPROVAL_COMMENT
