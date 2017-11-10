# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import os

from mozlogging import MozLogFormatter

logger = logging.getLogger(__name__)


def initialize_logging():
    """Initialize application-wide logging."""
    mozlog_handler = logging.StreamHandler()
    mozlog_handler.setFormatter(MozLogFormatter())

    # We need to configure the logger just for our application code.  This is
    # because the MozLogFormatter changes the signature of the standard
    # library logging functions.  Any code that tries to log a message assuming
    # the standard library's formatter is in place, such as the code in the
    # libraries we use, with throw an error if the MozLogFormatter tries to
    # handle the message.
    app_logger = logging.getLogger('landoui')

    # Stop our specially-formatted log messages from bubbling up to any
    # Flask-installed loggers that may be present.  They will throw an
    # exception if they handle our messages.
    app_logger.propagate = False

    app_logger.addHandler(mozlog_handler)

    level = os.environ.get('LOG_LEVEL', 'INFO')
    app_logger.setLevel(level)

    log_config_change('LOG_LEVEL', level)


def log_config_change(setting_name, value):
    """Helper to log configuration changes.

    Args:
        setting_name: The setting being changed.
        value: The setting's new value.
    """
    logger.info({'setting': setting_name, 'value': value}, 'app.configure')
