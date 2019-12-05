# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import render_template
import logging

from flask import (
    request,
    Blueprint,
    current_app,
    session,
)

from landoui.forms import UpliftApprovalForm, UpliftRequestForm
from landoui.helpers import (
    get_phabricator_api_token, set_last_local_referrer, oidc_auth_optional
)
from landoui.landoapi import LandoAPI, LandoAPIError
from landoui.errorhandlers import RevisionNotFound

logger = logging.getLogger(__name__)

uplift = Blueprint('uplift', __name__)
uplift.before_request(set_last_local_referrer)


def render_approval_comment(form_data: dict, source_revision_id=None) -> str:
    """
    Render the approval form as a Remarkup string
    * when source revision is provided, an uplift request form is rendered
    * otherwise an approval request form is rendered
    """
    return render_template(
        "uplift/comment.html",
        source_revision_id=source_revision_id,
        uplift=form_data
    )


@uplift.route('/uplift/request/D<int:revision_id>/', methods=('GET', 'POST'))
@oidc_auth_optional
def create(revision_id):
    """Render and submit an uplift request for a specific revision"""

    # Load the revision's entire stack
    api = LandoAPI(
        current_app.config['LANDO_API_URL'],
        auth0_access_token=session.get('access_token'),
        phabricator_api_token=get_phabricator_api_token(),
    )
    try:
        stack = api.request('GET', 'stacks/D{}'.format(revision_id))
    except LandoAPIError as e:
        if e.status_code == 404:
            raise RevisionNotFound(revision_id)
        else:
            raise

    # Build and process the form
    form = UpliftRequestForm(request.form)
    form.repository.choices = [
        (repo, repo) for repo in stack["uplift_repositories"]
    ]
    uplift_request = None
    if (request.method == 'POST' and api.has_phabricator_token()
            and form.validate()):

        # Send uplift request to backend
        uplift_request = api.request(
            'POST',
            'uplift',
            require_auth0=True,
            json={
                'revision_id':
                revision_id,
                'repository':
                form.data['repository'],
                'form_content':
                render_approval_comment(form.data, int(revision_id)),
            }
        )

    return render_template(
        'uplift/request.html',
        revision_id=revision_id,
        repositories=stack["uplift_repositories"],
        form=form,
        uplift_request=uplift_request,

        # Display a warning when phabricator is not available
        phabricator_token_available=api.has_phabricator_token(),
    )


@uplift.route('/uplift/approval/D<int:revision_id>/', methods=('GET', 'POST'))
@oidc_auth_optional
def approval(revision_id):
    """Render and submit an approval request for a specific revision"""

    # Load the revision's entire stack
    api = LandoAPI(
        current_app.config['LANDO_API_URL'],
        auth0_access_token=session.get('access_token'),
        phabricator_api_token=get_phabricator_api_token(),
    )
    try:
        stack = api.request('GET', 'stacks/D{}'.format(revision_id))
    except LandoAPIError as e:
        if e.status_code == 404:
            raise RevisionNotFound(revision_id)
        else:
            raise

    # Direct access to target revision
    revisions = {r["phid"]: r for r in stack["revisions"]}
    revision = next(
        (
            r for r in revisions.values()
            if r["id"] == "D{}".format(revision_id)
        ), None
    )

    # Load target repository from top landable revision
    repositories = {r['phid']: r for r in stack['repositories']}
    target_repo = None
    for p in stack["landable_paths"]:
        try:
            top_revision = p[:p.index(revision["phid"]) + 1][0]
            target_repo = repositories.get(
                revisions[top_revision]['repo_phid']
            )
        except (IndexError, ValueError):
            pass

    # Build and process the form
    form = UpliftApprovalForm(request.form)
    approval_request = None
    if (request.method == 'POST' and api.has_phabricator_token()
            and form.validate() and target_repo is not None):

        # Send uplift request to backend
        approval_request = api.request(
            'POST',
            'uplift',
            require_auth0=True,
            json={
                'revision_id': revision_id,
                'repository': target_repo["short_name"],
                'form_content': render_approval_comment(form.data),
            }
        )

    return render_template(
        'uplift/approval.html',
        revision_id=revision_id,
        repository=target_repo,
        form=form,
        approval_request=approval_request,

        # Display a warning when phabricator is not available
        phabricator_token_available=api.has_phabricator_token(),
    )
