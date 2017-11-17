# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from flask import (Blueprint)

filters = Blueprint('filters', __name__)


@filters.app_template_filter()
def select_reviewers(reviewers, *args):
    return [r for r in reviewers if r['status'] in args]


@filters.app_template_filter()
def tostatusbadgeclass(status):
    mapping = {
        'aborted': 'u-revision-badge--negative',
        'submitted': 'u-revision-badge--neutral',
        'landed': 'u-revision-badge--positive',
        'failed': 'u-revision-badge--negative'
    }
    return mapping.get(status['status'], 'u-revision-badge--negative')


@filters.app_template_filter()
def tostatusbadgename(status):
    mapping = {
        'aborted': 'Aborted',
        'submitted': 'Landing In Progress',
        'landed': 'Successfully Landed',
        'failed': 'Failed to Land'
    }
    return mapping.get(status['status'], status['status'].capitalize())
