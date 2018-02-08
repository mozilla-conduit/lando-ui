# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from flask import (Blueprint)

from landoui import helpers

template_helpers = Blueprint('template_helpers', __name__)


@template_helpers.app_template_global()
def is_user_authenticated():
    return helpers.is_user_authenticated()


@template_helpers.app_template_filter()
def select_reviewers(reviewers, *args):
    return [r for r in reviewers if r['status'] in args]


@template_helpers.app_template_filter()
def tostatusbadgeclass(status):
    mapping = {
        'aborted': 'u-revision-badge--negative',
        'submitted': 'u-revision-badge--warning',
        'landed': 'u-revision-badge--positive',
        'failed': 'u-revision-badge--negative'
    }
    return mapping.get(status['status'], 'u-revision-badge--negative')


@template_helpers.app_template_filter()
def tostatusbadgename(status):
    mapping = {
        'aborted': 'Aborted',
        'submitted': 'Landing Queued',
        'landed': 'Successfully Landed',
        'failed': 'Failed to Land'
    }
    return mapping.get(status['status'], status['status'].capitalize())


@template_helpers.app_template_filter()
def latest_status(statuses):
    if not statuses:
        return None

    statuses = sorted(statuses, key=lambda k: k['updated_at'], reverse=True)
    return statuses[0]['status']
