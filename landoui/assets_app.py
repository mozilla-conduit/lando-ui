# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
In order to build assets, the `flask assets build` command requires a
reference to a python file which has an `app` variable available to import.
This file provides that by initializing the flask app with basic configuration.
If you just want to build assets run `invoke build_assets`, the output can
be found in the landoui/static/build folder.
"""
import binascii
import os

from landoui.app import create_app

app = create_app(
    version_path='/version.json',
    secret_key=str(binascii.b2a_hex(os.urandom(15))),
    session_cookie_name='lando-ui.test',
    session_cookie_domain='lando-ui.test',
    session_cookie_secure=False,
    use_https=0,
    enable_asset_pipeline=True,
    lando_api_url='lando-api.test',
)
