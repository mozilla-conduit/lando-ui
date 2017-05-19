# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# mozlog specification used can be found at
# https://github.com/mozilla-services/Dockerflow/blob/master/docs/mozlog.md
import copy
import json
import logging

MOZLOG_ENVVERSION = '2.0'


class MozLogFormatter(logging.Formatter):
    """A mozlog logging formatter."""

    # Syslog severity levels.
    SYSLOG_EMERG = 0  # system is unusable
    SYSLOG_ALERT = 1  # action must be taken immediately
    SYSLOG_CRIT = 2  # critical conditions
    SYSLOG_ERR = 3  # error conditions
    SYSLOG_WARNING = 4  # warning conditions
    SYSLOG_NOTICE = 5  # normal but significant condition
    SYSLOG_INFO = 6  # informational
    SYSLOG_DEBUG = 7  # debug-level messages

    # Mapping from python logging priority to Syslog severity level.
    priority_map = {
        "DEBUG": SYSLOG_DEBUG,
        "INFO": SYSLOG_INFO,
        "WARNING": SYSLOG_WARNING,
        "ERROR": SYSLOG_ERR,
        "CRITICAL": SYSLOG_CRIT,
    }

    def serialize(self, mozlog_record):
        """Serialize a mozlog record."""
        return json.dumps(mozlog_record, sort_keys=True)

    def format(self, record):
        """Formats a log record and serializes to mozlog json"""
        mozlog_record = {
            # TODO: Add the Hostname.
            # 'Hostname': 'server-a123.mozilla.org',
            'Type': 'app.log',
            'EnvVersion': MOZLOG_ENVVERSION,
        }
        mozlog_record['Timestamp'] = int(record.created * 1000000000)
        mozlog_record['Logger'] = 'landoui.{}'.format(record.name)
        mozlog_record['Severity'] = self.priority_map.get(
            record.levelname, self.SYSLOG_WARNING
        )

        for arg in record.args:
            overrides = arg if isinstance(arg, dict) else {'Type': arg}
            mozlog_record.update(overrides)

        mozlog_record['Fields'] = (
            copy.copy(record.msg) if isinstance(record.msg, dict) else {
                'msg': record.msg
            }
        )

        if record.exc_info:
            mozlog_record['Fields']['exc_info'] = (
                self.formatException(record.exc_info)
            )

        return self.serialize(mozlog_record)


class PrettyMozLogFormatter(MozLogFormatter):
    """A mozlog logging formatter which pretty prints."""

    def serialize(self, mozlog_record):
        """Serialize a mozlog record."""
        return json.dumps(mozlog_record, sort_keys=True, indent=4)


def tornado_log_function(handler):
    """Log tornado access' in mozlog format.

    This logging function can be used to override the default tornado
    logging function for logging in the mozlog format.
    """
    status_code = handler.get_status()
    fields = {
        'errno': (0 if status_code < 400 else status_code),
        'status': status_code,
        'method': handler.request.method,
        'path': handler.request.path,
        't': int(handler.request.request_time() * 1000),
        # TODO: This should include the entire chain of
        # addresses between the client and server.
        'remoteAddressChain': [handler.request.remote_ip]
        # TODO: Add the user id when we actually
        # have access to it.
        # 'uid': '12345'
    }

    agent = handler.request.headers.get('User-Agent')
    if agent is not None:
        fields['agent'] = agent

    logging.getLogger('tornado.access').info(fields, 'request.summary')


def get_mozlog_config(debug=False, pretty=False):
    """Return a logging config appropriate for mozlog."""
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'mozlog': {
                '()': (PrettyMozLogFormatter if pretty else MozLogFormatter),
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'mozlog',
            },
        },
        'loggers': {
            'tornado.access': {
                'level': ('DEBUG' if debug else 'INFO'),
                'propagate': True,
            },
        },
        'root': {
            'level': ('DEBUG' if debug else 'INFO'),
            'handlers': ['console']
        }
    }
