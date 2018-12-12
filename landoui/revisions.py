# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import functools
import json
import logging

from flask import (
    Blueprint,
    current_app,
    render_template,
    redirect,
    session,
    url_for,
)

from landoui.app import oidc
from landoui.forms import RevisionForm, TransplantRequestForm
from landoui.helpers import (
    get_phabricator_api_token, is_user_authenticated, set_last_local_referrer
)
from landoui.landoapi import LandoAPI, LandoAPIError
from landoui.landoapiclient import LandoAPIClient, LandingSubmissionError
from landoui.errorhandlers import RevisionNotFound
from landoui.stacks import draw_stack_graph, Edge, sort_stack_topological

logger = logging.getLogger(__name__)

revisions = Blueprint('revisions', __name__)
revisions.before_request(set_last_local_referrer)


def oidc_auth_optional(f):
    """Decorator that runs auth only if the user is logged in."""
    no_auth_f = f
    auth_f = oidc.oidc_auth(f)

    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not is_user_authenticated():
            handler = no_auth_f
        else:
            handler = auth_f

        return handler(*args, **kwargs)

    return wrapped


@revisions.route('/D<int:revision_id>/', methods=('GET', 'POST'))
@oidc_auth_optional
def revision(revision_id):
    api = LandoAPI(
        current_app.config['LANDO_API_URL'],
        auth0_access_token=session.get('access_token'),
        phabricator_api_token=get_phabricator_api_token()
    )

    form = TransplantRequestForm()
    errors = []
    if form.is_submitted():
        if not is_user_authenticated():
            errors.append('You must be logged in to request a landing')

        elif not form.validate():
            for _, field_errors in form.errors.items():
                errors.extend(field_errors)

        else:
            try:
                api.request(
                    'POST',
                    'transplants',
                    require_auth0=True,
                    json={
                        'landing_path': json.loads(form.landing_path.data),
                        'confirmation_token': form.confirmation_token.data,
                    }
                )
                # We don't actually need any of the data from the
                # the submission. As long as an exception wasn't
                # raised we're successful.
                return redirect(
                    url_for('revisions.revision', revision_id=revision_id)
                )
            except LandoAPIError as e:
                if not e.detail:
                    raise

                errors.append(e.detail)

    # Request the entire stack.
    try:
        stack = api.request('GET', 'stacks/D{}'.format(revision_id))
    except LandoAPIError as e:
        if e.status_code == 404:
            raise RevisionNotFound(revision_id)
        else:
            raise

    # Build a mapping from phid to revision and identify
    # the data for the revision used to load this page.
    revision = None
    revisions = {}
    for r in stack['revisions']:
        revisions[r['phid']] = r
        if r['id'] == 'D{}'.format(revision_id):
            revision = r['phid']

    # Request all previous transplants for the stack.
    transplants = api.request(
        'GET',
        'transplants',
        params={'stack_revision_id': 'D{}'.format(revision_id)}
    )

    # The revision may appear in many `landable_paths`` if it has
    # multiple children, or any of its landable descendents have
    # multiple children. That being said, there should only be a
    # single unique path up to this revision, so find the first
    # it appears in. The revisions up to the target one in this
    # path form the landable series.
    #
    # We also form a set of all the revisions that are landable
    # so we can present selection for what to land.
    series = None
    landable = set()
    for p in stack['landable_paths']:
        for phid in p:
            landable.add(phid)

        try:
            series = p[:p.index(revision) + 1]
        except ValueError:
            pass

    dryrun = None
    if series and is_user_authenticated():
        landing_path = [
            {
                'revision_id': revisions[phid]['id'],
                'diff_id': revisions[phid]['diff']['id'],
            } for phid in series
        ]
        form.landing_path.data = json.dumps(landing_path)

        dryrun = api.request(
            'POST',
            'transplants/dryrun',
            require_auth0=True,
            json={'landing_path': landing_path}
        )
        form.confirmation_token.data = dryrun.get('confirmation_token')

        series = list(reversed(series))

    phids = set(revisions.keys())
    edges = set(Edge(child=e[0], parent=e[1]) for e in stack['edges'])
    order = sort_stack_topological(
        phids, edges, key=lambda x: int(revisions[x]['id'][1:])
    )
    drawing_width, drawing_rows = draw_stack_graph(phids, edges, order)

    return render_template(
        'stack/stack.html',
        revision_id='D{}'.format(revision_id),
        series=series,
        landable=landable,
        dryrun=dryrun,
        stack=stack,
        rows=list(zip(reversed(order), reversed(drawing_rows))),
        drawing_width=drawing_width,
        transplants=transplants,
        revisions=revisions,
        revision_phid=revision,
        errors=errors,
        form=form,
    )


@revisions.route(
    '/revisions/<revision_id>/<diff_id>/', methods=('GET', 'POST')
)
@revisions.route('/revisions/<revision_id>/')
@oidc_auth_optional
def revisions_handler(revision_id, diff_id=None):
    landoapi = LandoAPIClient(
        landoapi_url=current_app.config['LANDO_API_URL'],
        phabricator_api_token=get_phabricator_api_token(),
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
