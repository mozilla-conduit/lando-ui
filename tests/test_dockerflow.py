# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import binascii

import click
import pytest

from landoui.app import create_app


@pytest.fixture
def versionfile(tmpdir):
    """Provide a temporary version.json on disk."""
    v = tmpdir.mkdir('app').join('version.json')
    v.write(
        json.dumps(
            {
                'source': 'https://github.com/mozilla-conduit/lando-api',
                'version': '0.0.0',
                'commit': '',
                'build': 'test',
            }
        )
    )
    return v


@pytest.fixture
def app(versionfile):
    """Needed for pytest-flask."""
    return click.Context.invoke(
        None,
        create_app,
        run_dev_server=False,
        debug=True,
        port=80,
        host='0.0.0.0',
        version_path=versionfile.strpath,
        secret_key=str(binascii.b2a_hex(os.urandom(15))),
        session_cookie_name='lando-ui',
        session_cookie_domain='lando-ui:7777',
        session_cookie_secure=False,
    )


def test_dockerflow_lb_endpoint_returns_200(client):
    assert client.get('/__lbheartbeat__').status_code == 200


def test_dockerflow_heartbeat_endpoint_returns_200(client):
    assert client.get('/__heartbeat__').status_code == 200


def test_dockerflow_version_endpoint_response(client):
    response = client.get('/__version__')
    assert response.status_code == 200
    assert response.content_type == 'application/json'


def test_dockerflow_version_matches_disk_contents(client, versionfile):
    response = client.get('/__version__')
    assert response.json == json.load(versionfile.open())
