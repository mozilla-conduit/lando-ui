# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json

import logging
import requests
from flask import Blueprint, current_app, jsonify

logger = logging.getLogger(__name__)

dockerflow = Blueprint('dockerflow', __name__)


@dockerflow.route('/__heartbeat__')
def heartbeat():
    """Perform health check of lando-ui.

    This should check all the services that lando-ui depends on
    and return a 200 iff those services and the app itself are
    performing normally. Return a 5XX if something goes wrong.
    """
    try:
        response = requests.get(
            current_app.config['LANDO_API_URL'] + '/__lbheartbeat__'
        )
        response.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError):
        logger.warning(
            {
                'msg': 'problem connecting to lando-api',
            }, 'heartbeat'
        )
        return 'heartbeat: problem', 500
    logger.info({'msg': 'ok, all services are up'}, 'heartbeat')
    return 'heartbeat: ok', 200


@dockerflow.route('/__lbheartbeat__')
def lbheartbeat():
    """Perform health check for load balancer.

    Since this is for load balancer checks it should not check
    backing services.
    """
    return '', 200


@dockerflow.route('/__version__')
def version():
    """Respond with version information as defined by /app/version.json."""
    try:
        with open(current_app.config['VERSION_PATH']) as f:
            return jsonify(json.load(f))
    except (IOError, ValueError):
        # TODO log error
        return 'Unable to load version.json', 500
