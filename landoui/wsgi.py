# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Construct an application instance that can be referenced by a WSGI server.
"""
import os

from .app import create_app
from .helpers import str2bool

app = create_app(
    version_path=os.getenv("VERSION_PATH"),
    secret_key=os.getenv("SECRET_KEY"),
    session_cookie_name=os.getenv("SESSION_COOKIE_NAME"),
    session_cookie_domain=os.getenv("SESSION_COOKIE_DOMAIN"),
    session_cookie_secure=str2bool(os.getenv("SESSION_COOKIE_SECURE", 1)),
    use_https=str2bool(os.getenv("USE_HTTPS", 1)),
    enable_asset_pipeline=True,
    lando_api_url=os.getenv("LANDO_API_URL"),
    treestatus_url=os.getenv("TREESTATUS_URL"),
    debug=str2bool(os.getenv("DEBUG", 0)),
)
