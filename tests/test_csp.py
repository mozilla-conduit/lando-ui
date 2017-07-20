# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def test_csp_headers_set(client):
    response = client.get('/')
    assert 'Content-Security-Policy' in response.headers
    # Ensure we're using the most secure source by default
    assert "default-src 'self'" in response.headers['Content-Security-Policy']
