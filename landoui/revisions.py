# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os

import requests

from flask import (
    abort, Blueprint, current_app, jsonify, redirect, render_template, session
)

from landoui.helpers import set_last_local_referrer
from landoui.sentry import sentry

revisions = Blueprint('revisions', __name__)
revisions.before_request(set_last_local_referrer)


@revisions.route('/revisions/<revision_id>')
def get_revision(revision_id):
    revision_api_url = '{}/revisions/{}'.format(
        os.getenv('LANDO_API_URL'), revision_id
    )

    try:
        result = requests.get(revision_api_url)
        result.raise_for_status()
    except requests.HTTPError as exc:
        if exc.response.status_code == 404:
            # The user looked up a non-existent revision, no special treatment
            # is necessary.
            abort(404)
        else:
            sentry.captureException()
            abort(500)
    except requests.ConnectionError:
        sentry.captureException()
        abort(500)

    revision = result.json()

    return render_template(
        'revision.html',
        revision=revision,
        author=revision['author'],
        repo=revision['repo'],
        parents=_flatten_parent_revisions(revision)
    )


def _flatten_parent_revisions(revision):
    """ Transforms a JSON tree of parent revisions into a flat array.

    Args:
        revision: A revision (hash) which has parent revisions, which
            can themselves have parent revisions, and so on.
    Returns:
        A new array containing the parent revisions in breath first order.
    """
    parents = revision.get('parent_revisions', [])
    parents_of_parents = []
    for parent in parents:
        parents_of_parents += _flatten_parent_revisions(parent)
    return parents + parents_of_parents
