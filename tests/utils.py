# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import binascii
import json

import click
import pytest

from landoui.app import create_app


@pytest.fixture
def app(versionfile):
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
        session_cookie_domain='lando-ui.test:7777',
        session_cookie_secure=False,
        use_https=0
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
