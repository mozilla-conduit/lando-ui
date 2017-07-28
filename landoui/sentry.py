# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os

from raven.contrib.flask import Sentry

from landoui.logging import log_config_change


def initialize_sentry(app, release):
    """Initialize Sentry application monitoring.

    See https://docs.sentry.io/clients/python/advanced/#client-arguments for
    details about what this function's arguments mean to Sentry.

    Args:
        app: A Flask() instance.
        release: A string representing this application release number (such as
            a git sha).  Will be used as the Sentry "release" identifier. See
            the Sentry client configuration docs for details.
    """
    sentry_dsn = os.environ.get('SENTRY_DSN', None)
    if sentry_dsn:
        log_config_change('SENTRY_DSN', sentry_dsn)
    else:
        log_config_change('SENTRY_DSN', 'none (sentry disabled)')

    # Do this after logging the DSN so if there is a DSN URL parsing error
    # the logs will record the configured value before the Sentry client
    # kills the app.
    sentry = Sentry(app, dsn=sentry_dsn)

    # Set these attributes directly because their keyword arguments can't be
    # passed into Sentry.__init__() or make_client().
    sentry.client.release = release
    log_config_change('SENTRY_LOG_RELEASE_AS', release)

    environment = os.environ.get('ENV', None)
    sentry.client.environment = environment
    log_config_change('SENTRY_LOG_ENVIRONMENT_AS', environment)
