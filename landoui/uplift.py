# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import render_template


def render_uplift_comment(source_revision_id: int, form_data: dict) -> str:
    """
    Render the uplift form as a Remarkup string
    This is used to populate the new revision's summary
    """
    return render_template(
        "uplift/comment.html",
        source_revision_id=source_revision_id,
        uplift=form_data
    )
