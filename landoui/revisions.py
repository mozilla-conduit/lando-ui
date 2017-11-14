# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import requests

from flask import (abort, Blueprint, current_app, render_template)

from landoui.forms import RevisionForm
from landoui.helpers import set_last_local_referrer
from landoui.sentry import sentry

revisions = Blueprint('revisions', __name__)
revisions.before_request(set_last_local_referrer)


@revisions.route('/revisions/<revision_id>', methods=('GET', 'POST'))
def revision(revision_id):
    revision_api_url = '{}/revisions/{}'.format(
        current_app.config['LANDO_API_URL'], revision_id
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

    form = RevisionForm()
    if form.is_submitted():
        if form.validate():
            # TODO
            # Any more validation and then request to API
            pass
        else:
            # TODO
            # Return validation errors
            pass

    # Set the diff id explicitly to avoid timing conflicts with
    # revision diff IDs being updated
    form.diff_id.data = revision['diff']['id']

    return render_template(
        'revision.html',
        revision=revision,
        author=revision['author'],
        repo=revision['repo'],
        parents=_flatten_parent_revisions(revision),
        form=form
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
