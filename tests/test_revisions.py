# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import requests_mock

from tests.canned_responses import canned_landoapi


def test_render_valid_revision(client, api_url):
    with requests_mock.mock() as m:
        m.get(
            api_url + '/landings?revision_id=D1',
            json=canned_landoapi.GET_LANDINGS_DEFAULT
        )
        m.get(
            api_url + '/revisions/D1',
            json=canned_landoapi.GET_REVISION_DEFAULT
        )
        response = client.get('/revisions/D1')
    assert response.status_code == 200


def test_missing_revision_returns_404(client, api_url):
    with requests_mock.mock() as m:
        m.get(api_url + '/revisions/D1057', status_code=404)
        response = client.get('/revisions/D1057')
    assert response.status_code == 404
    assert b'Revision/Diff Not Available' in response.get_data()


def test_lando_api_500_response_shows_error_page(client, api_url):
    with requests_mock.mock() as m:
        m.get(api_url + '/revisions/D1', status_code=500)
        response = client.get('/revisions/D1')
        assert response.status_code == 500
        assert b'Failed to reach Lando API' in response.get_data()
