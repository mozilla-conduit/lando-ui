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
import os
import binascii

import click

from landoui.app import create_app

app = click.Context.invoke(
    None,
    create_app,
    run_dev_server=False,
    debug=True,
    port=80,
    host='0.0.0.0',
    version_path='/version.json',
    secret_key=str(binascii.b2a_hex(os.urandom(15))),
    session_cookie_name='landoui-development-app',
    session_cookie_domain='',
    session_cookie_secure=False,
)
