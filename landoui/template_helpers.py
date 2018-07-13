# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import urllib.parse

from flask import (Blueprint)

from landoui import helpers

logger = logging.getLogger(__name__)
template_helpers = Blueprint('template_helpers', __name__)


@template_helpers.app_template_global()
def is_user_authenticated():
    return helpers.is_user_authenticated()


@template_helpers.app_template_filter()
def select_reviewers(reviewers, *args, other_diffs=None):
    if args:
        reviewers = [r for r in reviewers if r['status'] in args]

    if other_diffs is not None:
        reviewers = [
            r for r in reviewers if r['for_other_diff'] == other_diffs
        ]

    return reviewers


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


@template_helpers.app_template_filter()
def avatar_url(url):
    # If a user doesn't have a gravatar image for their auth0 email address,
    # gravatar uses auth0's provided default which redirects to
    # *.wp.com/cdn.auth0.com/. Instead of whitelisting this in our CSP,
    # here, we opt into a default generated image provided by gravatar.
    try:
        parsed_url = urllib.parse.urlsplit(url)
        if not parsed_url.netloc:
            raise ValueError('Avatar URLs should not be relative')
    except (AttributeError, ValueError):
        logger.debug('Invalid avatar url provided', extra={'url': url})
        return ''

    if parsed_url.netloc in ('s.gravatar.com', 'www.gravatar.com'):
        query = urllib.parse.parse_qs(parsed_url.query)
        query['d'] = 'identicon'
        parsed_url = (
            parsed_url[:3] +
            (urllib.parse.urlencode(query, doseq=True), ) + parsed_url[4:]
        )

    return urllib.parse.urlunsplit(parsed_url)
