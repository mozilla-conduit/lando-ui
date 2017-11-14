# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest

from werkzeug.datastructures import MultiDict

from landoui.forms import RevisionForm


class MockRevisionForm(RevisionForm):
    class Meta:
        csrf = False

@pytest.mark.parametrize(
    'diff_id,is_valid', [
        ('', False),
        ('12L34', False),
        ('12345', True),
    ]
) # yapf: disable
def test_revision_form_diff_id(app, diff_id, is_valid):
    with app.app_context():
        form = MockRevisionForm(MultiDict((('diff_id', diff_id), )))
        assert form.validate() == is_valid
