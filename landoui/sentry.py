# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from landoui.logging import log_config_change


def sanitize_headers(headers: dict[str, str]):
    """Filter security sensitive values from headers.

    Note that this updates the values from `headers` in-place.
    """
    sensitive_keys = ("X-PHABRICATOR-API-KEY",)
    for key in headers:
        if key.upper() in sensitive_keys:
            headers[key] = 10 * "*"


def before_send(event: dict, *args) -> dict:
    """Sentry callback to filter event data before sending."""
    if "request" in event and "headers" in event["request"]:
        sanitize_headers(event["request"]["headers"])
    return event


def initialize_sentry(release: str):
    """Initialize Sentry application monitoring.

    Args:
        release: A string representing this application release number (such as
            a git sha).  Will be used as the Sentry "release" identifier. See
            the Sentry client configuration docs for details.
    """
    sentry_dsn = os.environ.get("SENTRY_DSN", None)
    if sentry_dsn:
        log_config_change("SENTRY_DSN", "********")
    else:
        log_config_change("SENTRY_DSN", "none (sentry disabled)")

    # Log release.
    log_config_change("SENTRY_LOG_RELEASE_AS", release)

    # Log environment.
    environment = os.environ.get("ENV", None)
    log_config_change("SENTRY_LOG_ENVIRONMENT_AS", environment)

    sentry_sdk.init(
        before_send=before_send,
        dsn=sentry_dsn,
        environment=environment,
        integrations=[FlaskIntegration()],
        release=release,
        traces_sample_rate=1.0,
    )
