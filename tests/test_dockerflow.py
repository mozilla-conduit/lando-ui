# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

import requests
import requests_mock


def test_dockerflow_lb_endpoint_returns_200(client):
    assert client.get("/__lbheartbeat__").status_code == 200


def test_heartbeat_returns_200_if_lando_api_up(client, api_url):
    with requests_mock.mock() as m:
        m.get(api_url + "/__lbheartbeat__", status_code=200)
        assert client.get("/__heartbeat__").status_code == 200


def test_heartbeat_returns_502_if_lando_api_down(client, api_url):
    with requests_mock.mock() as m:
        m.get(api_url + "/__lbheartbeat__", exc=requests.ConnectionError)
        assert client.get("/__heartbeat__").status_code == 502


def test_dockerflow_version_endpoint_response(client):
    response = client.get("/__version__")
    assert response.status_code == 200
    assert response.content_type == "application/json"


def test_dockerflow_version_matches_disk_contents(client, versionfile):
    response = client.get("/__version__")
    assert response.json == json.load(versionfile.open())
