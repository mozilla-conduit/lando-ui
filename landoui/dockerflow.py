# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import time

import requests
from flask import Blueprint, current_app, g, jsonify, request

logger = logging.getLogger(__name__)
request_logger = logging.getLogger("request.summary")

dockerflow = Blueprint("dockerflow", __name__)


@dockerflow.after_request
def disable_caching(response):
    """Disable caching on a response and return it."""
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    return response


@dockerflow.before_app_request
def request_logging_before():
    g._request_start_timestamp = time.time()


@dockerflow.after_app_request
def request_logging_after(response):
    summary = {
        "errno": 0 if response.status_code < 400 else 1,
        "agent": request.headers.get("User-Agent", ""),
        "lang": request.headers.get("Accept-Language", ""),
        "method": request.method,
        "path": request.path,
        "code": response.status_code,
    }

    start = g.get("_request_start_timestamp", None)
    if start is not None:
        summary["t"] = int(1000 * (time.time() - start))

    request_logger.info("request summary", extra=summary)

    return response


@dockerflow.route("/__heartbeat__")
def heartbeat():
    """Perform health check of lando-ui.

    This should check all the services that lando-ui depends on
    and return a 200 iff those services and the app itself are
    performing normally. Return a 5XX if something goes wrong.
    """
    try:
        response = requests.get(
            current_app.config["LANDO_API_URL"] + "/__lbheartbeat__"
        )
        response.raise_for_status()
        healthy = True
    except (requests.HTTPError, requests.ConnectionError) as exc:
        logger.warning(
            "unhealthy: problem with backing service",
            extra={
                "service_name": "lando_api",
                "errors": ["requests.RequestException: {!s}".format(exc)],
            },
        )
        healthy = False

    return (
        jsonify({"healthy": healthy, "services": {"lando_api": healthy,},}),
        200 if healthy else 502,
    )


@dockerflow.route("/__lbheartbeat__")
def lbheartbeat():
    """Perform health check for load balancer.

    Since this is for load balancer checks it should not check
    backing services.
    """
    return "", 200


@dockerflow.route("/__version__")
def version():
    """Respond with version information as defined in the app config."""
    return jsonify(current_app.config["VERSION"])
