# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import urllib.parse

import pytest

from landoui.template_helpers import avatar_url


@pytest.mark.parametrize(
    'input_url,output_url',
    [
        (
            'https://lh3.googleusercontent.com/-ABCDef/123/photo.jpg',
            'https://lh3.googleusercontent.com/-ABCDef/123/photo.jpg'
        ),
        (
            'https://s.gravatar.com/avatar/9b665?s=480&r=pg&d=https%3A%2F%2Fcdn.auth0.com%2Favatars%2Fcs.png',  # noqa
            'https://s.gravatar.com/avatar/9b665?s=480&r=pg&d=identicon',
        ),
        (
            'https://s.gravatar.com/avatar/123b',
            'https://s.gravatar.com/avatar/123b?d=identicon'
        ),
        (
            '//www.gravatar.com/avatar/123b?s=480&r=pg&d=robohash',
            '//www.gravatar.com/avatar/123b?s=480&r=pg&d=identicon'
        ),
        ('/relative_path_only', ''),
        ('1 invalid url', ''),
        (9000, ''),
    ]
)
def test_avatar_url(input_url, output_url):
    # Query params are not guaranteed to be in the same order, so
    # we cannot do string comparison of the URLs.
    expected = urllib.parse.urlparse(output_url)
    actual = urllib.parse.urlparse(avatar_url(input_url))
    expected_qs = urllib.parse.parse_qs(expected.query)
    actual_qs = urllib.parse.parse_qs(actual.query)

    for argument in expected_qs:
        assert expected_qs[argument] == actual_qs[argument]

    assert (expected.scheme, expected.netloc, expected.path) == \
           (actual.scheme, actual.netloc, actual.path)
