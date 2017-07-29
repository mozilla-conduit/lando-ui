# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import requests
import requests_mock

from tests.canned_responses import LANDO_API_RESPONSE


def test_render_valid_revision(client, monkeypatch):
    monkeypatch.setenv('LANDO_API_URL', 'http://landoapi.test')
    with requests_mock.mock() as m:
        m.get('http://landoapi.test/revisions/D1', json=LANDO_API_RESPONSE)
        response = client.get('/revisions/D1')
    assert response.status_code == 200


def test_missing_revision_returns_404(client, monkeypatch):
    monkeypatch.setenv('LANDO_API_URL', 'http://landoapi.test')
    with requests_mock.mock() as m:
        m.get('http://landoapi.test/revisions/D1057', status_code=404)
        response = client.get('/revisions/D1057')
    assert response.status_code == 404


def test_lando_api_connection_error_returns_500(client, monkeypatch):
    monkeypatch.setenv('LANDO_API_URL', 'http://landoapi.test')
    with requests_mock.mock() as m:
        m.get(
            'http://landoapi.test/revisions/D1', exc=requests.ConnectionError
        )
        response = client.get('/revisions/D1')
    assert response.status_code == 500


def test_lando_api_response_insanity_returns_500(client, monkeypatch):
    monkeypatch.setenv('LANDO_API_URL', 'http://landoapi.test')
    with requests_mock.mock() as m:
        m.get('http://landoapi.test/revisions/D1', status_code=500)
        response = client.get('/revisions/D1')
    assert response.status_code == 500
