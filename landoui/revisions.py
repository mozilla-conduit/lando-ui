# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging

from flask import Blueprint, current_app, render_template, redirect, session

from landoui.forms import RevisionForm
from landoui.helpers import is_user_authenticated, set_last_local_referrer
from landoui.landoapiclient import LandoAPIClient, LandingSubmissionError

logger = logging.getLogger(__name__)

revisions = Blueprint('revisions', __name__)
revisions.before_request(set_last_local_referrer)


@revisions.route('/revisions/<revision_id>/<diff_id>', methods=('GET', 'POST'))
@revisions.route('/revisions/<revision_id>')
def revisions_handler(revision_id, diff_id=None):
    landoapi = LandoAPIClient(
        landoapi_url=current_app.config['LANDO_API_URL'],
        phabricator_api_token=None,
        auth0_access_token=session.get('access_token')
    )

    # Loads the submitted form if POST or creates a new one if GET
    form = RevisionForm()
    errors = []

    # Submit the landing request if this is a POST
    if form.is_submitted():
        if form.validate():
            try:
                # Returns True or raises a LandingSubmissionError
                if landoapi.post_landings(revision_id, form.diff_id.data):
                    redirect_url = '/revisions/{revision_id}/{diff_id}'.format(
                        revision_id=revision_id, diff_id=diff_id
                    )
                    return redirect(redirect_url)
            except LandingSubmissionError as e:
                errors.append(e.error)
        else:
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(error)

    # If this is a GET or the POST fails, load data to display revision page.
    revision = landoapi.get_revision(revision_id, diff_id)
    parent_revisions = _flatten_parent_revisions(revision)
    landing_statuses = landoapi.get_landings(revision_id)
    dryrun_result = {}
    if is_user_authenticated():
        dryrun_result = landoapi.post_landings_dryrun(revision_id, diff_id)
        # TODO: Save the dryrun confirmation token in the form so it is
        # used when making the real landing request.
    form.diff_id.data = revision['diff']['id']

    return render_template(
        'revision/revision.html',
        revision=revision,
        landing_statuses=landing_statuses,
        parents=parent_revisions,
        form=form,
        dryrun_confirmation_token=dryrun_result.get('confirmation_token'),
        warnings=dryrun_result.get('warnings', []),
        blockers=dryrun_result.get('blockers', []),
        errors=errors
    )


def _flatten_parent_revisions(revision):
    """ Transforms a JSON tree of parent revisions into a flat array.

    Args:
        revision: A revision (dictionary) which has parent revisions, which
            can themselves have parent revisions, and so on.
    Returns:
        A new array containing the parent revisions in breath first order.
    """
    parents = revision.get('parent_revisions', [])
    parents_of_parents = []
    for parent in parents:
        parents_of_parents += _flatten_parent_revisions(parent)
    return parents + parents_of_parents
