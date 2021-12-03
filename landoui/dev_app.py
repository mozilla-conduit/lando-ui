# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import os

from landoui.app import create_app
from landoui.helpers import str2bool

logger = logging.getLogger(__name__)


def create_dev_app(**kwargs):
    """Create the development server for Flask."""
    params = {
        "debug": False,
        "version_path": "/app/version.json",
        "secret_key": None,
        "session_cookie_name": None,
        "session_cookie_domain": None,
        "session_cookie_secure": True,
        "use_https": True,
        "enable_asset_pipeline": True,
        "lando_api_url": None,
    }

    # These are parameters that should be converted to a boolean value.
    bool_param_keys = (
        "debug",
        "session_cookie_secure",
        "use_https",
        "enable_asset_pipeline",
    )

    for key in params:
        # Replace configuration defaults with environment variables.
        if key.upper() in os.environ:
            params[key] = os.environ[key.upper()]

    # Replace configuration parameters with keyword arguments.
    params.update(kwargs)

    # Guess boolean value based on string input.
    for bool_param in bool_param_keys:
        if bool_param in params and not isinstance(params[bool_param], bool):
            params[bool_param] = str2bool(params[bool_param])

    app = create_app(**params)
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    return app


app = create_dev_app()
