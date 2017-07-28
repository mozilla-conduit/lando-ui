# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import binascii
import json

import logging
import pytest

from landoui.app import create_app


@pytest.fixture
def docker_env_vars(monkeypatch):
    """Monkeypatch environment variables that we'd get running under docker."""
    monkeypatch.setenv('OIDC_DOMAIN', 'test_oidc_domain')
    monkeypatch.setenv('OIDC_CLIENT_ID', 'test_oidc_client_id')
    monkeypatch.setenv('OIDC_CLIENT_SECRET', 'test_oidc_secret')


@pytest.fixture
def disable_log_output():
    """Disable Python standard logging output to the console."""
    logging.disable(logging.CRITICAL)


@pytest.fixture
def app(versionfile, disable_log_output, docker_env_vars):
    return create_app(
        version_path=versionfile.strpath,
        secret_key=str(binascii.b2a_hex(os.urandom(15))),
        session_cookie_name='lando-ui',
        session_cookie_domain='lando-ui.test:7777',
        session_cookie_secure=False,
        use_https=0,
        enable_asset_pipeline=False
    )


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
