# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging

from flask import Blueprint, current_app, render_template, redirect, session

from landoui.app import oidc
from landoui.forms import RevisionForm
from landoui.helpers import is_user_authenticated, set_last_local_referrer
from landoui.landoapiclient import LandoAPIClient, LandingSubmissionError

logger = logging.getLogger(__name__)

revisions = Blueprint('revisions', __name__)
revisions.before_request(set_last_local_referrer)


@revisions.route(
    '/revisions/<revision_id>/<diff_id>/', methods=('GET', 'POST')
)
@revisions.route('/revisions/<revision_id>/')
def revisions_handler(revision_id, diff_id=None):
    if not is_user_authenticated():
        handler = _revisions_handler
    else:
        handler = _revisions_handler_with_auth

    return handler(revision_id, diff_id=diff_id)


def _revisions_handler(revision_id, diff_id=None):
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
        if not is_user_authenticated():
            errors.append('You must be logged in to land a revision.')
        elif form.validate():
            try:
                # Returns True or raises a LandingSubmissionError
                if landoapi.post_landings(
                    revision_id, form.diff_id.data,
                    form.confirmation_token.data
                ):
                    redirect_url = (
                        '/revisions/{revision_id}/{diff_id}/'.format(
                            revision_id=revision_id, diff_id=diff_id
                        )
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
    diff_id = diff_id or revision['diff']['id']
    landing_statuses = landoapi.get_landings(revision_id)
    dryrun_result = {}
    if is_user_authenticated():
        dryrun_result = landoapi.post_landings_dryrun(revision_id, diff_id)
        form.confirmation_token.data = dryrun_result.get('confirmation_token')

    form.diff_id.data = diff_id

    return render_template(
        'revision/revision.html',
        revision=revision,
        landing_statuses=landing_statuses,
        form=form,
        warnings=dryrun_result.get('warnings', []),
        blockers=dryrun_result.get('blockers', []),
        errors=errors
    )


_revisions_handler_with_auth = oidc.oidc_auth(_revisions_handler)
