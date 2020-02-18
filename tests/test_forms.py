# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest

from werkzeug.datastructures import MultiDict

from landoui.forms import UserSettingsForm


class MockUserSettingsForm(UserSettingsForm):
    class Meta:
        csrf = False


@pytest.mark.parametrize(
    "phab_api_token,is_valid",
    [
        ("", True),
        ("api-123456789012345678901234567x", True),
        ("api-123", False),
        ("xxx", False),
        ("xxx-123456789012345678901234567x", False),
        ("api-123456789012345678901234567X", False),
    ],
)  # yapf: disable
def test_user_settings(app, phab_api_token, is_valid):
    with app.app_context():
        form = MockUserSettingsForm(MultiDict((("phab_api_token", phab_api_token),)))
        assert form.validate() == is_valid
