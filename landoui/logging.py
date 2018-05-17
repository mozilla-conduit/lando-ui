# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import logging
import socket
import traceback

logger = logging.getLogger(__name__)


class MozLogFormatter(logging.Formatter):
    """A mozlog logging formatter.

    https://wiki.mozilla.org/Firefox/Services/Logging#MozLog_application_logging_standard
    """

    MOZLOG_ENVVERSION = '2.0'

    # Syslog severity levels.
    SL_EMERG = 0  # system is unusable
    SL_ALERT = 1  # action must be taken immediately
    SL_CRIT = 2  # critical conditions
    SL_ERR = 3  # error conditions
    SL_WARNING = 4  # warning conditions
    SL_NOTICE = 5  # normal but significant condition
    SL_INFO = 6  # informational
    SL_DEBUG = 7  # debug-level messages

    # Mapping from python logging priority to Syslog severity level.
    PRIORITY = {
        "DEBUG": SL_DEBUG,
        "INFO": SL_INFO,
        "WARNING": SL_WARNING,
        "ERROR": SL_ERR,
        "CRITICAL": SL_CRIT,
    }

    BUILTIN_LOGRECORD_ATTRIBUTES = set(
        (
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'msg', 'name', 'pathname', 'process', 'processName',
            'relativeCreated', 'stack_info', 'thread', 'threadName'
        )
    )

    def __init__(self, *args, mozlog_logger=None, **kwargs):
        self.mozlog_logger = mozlog_logger or 'Dockerflow'
        self.hostname = socket.gethostname()
        super().__init__(*args, **kwargs)

    def format(self, record):
        """Formats a log record and serializes to mozlog json"""

        mozlog_record = {
            'EnvVersion': self.MOZLOG_ENVVERSION,
            'Hostname': self.hostname,
            'Logger': self.mozlog_logger,
            'Type': record.name,
            'Timestamp': int(record.created * 1e9),
            'Severity': self.PRIORITY.get(record.levelname, self.SL_WARNING),
            'Pid': record.process,
            'Fields': {
                k: v
                for k, v in record.__dict__.items()
                if k not in self.BUILTIN_LOGRECORD_ATTRIBUTES
            }
        }

        msg = record.getMessage()
        if msg and 'msg' not in mozlog_record['Fields']:
            mozlog_record['Fields']['msg'] = msg

        if record.exc_info is not None:
            mozlog_record['Fields']['exc'] = {
                'error': repr(record.exc_info[1]),  # Instance
                'traceback': ''.join(traceback.format_tb(record.exc_info[2])),
            }

        return self.serialize(mozlog_record)

    def serialize(self, mozlog_record):
        """Serialize a mozlog record."""
        return json.dumps(mozlog_record, sort_keys=True)


class PrettyMozLogFormatter(MozLogFormatter):
    """A mozlog logging formatter which pretty prints."""

    def serialize(self, mozlog_record):
        """Serialize a mozlog record."""
        return json.dumps(mozlog_record, sort_keys=True, indent=2)


def log_config_change(setting_name, value):
    """Helper to log configuration changes.

    Args:
        setting_name: The setting being changed.
        value: The setting's new value.
    """
    logger.info(
        'app configuration', extra={
            'setting': setting_name,
            'value': value,
        }
    )
