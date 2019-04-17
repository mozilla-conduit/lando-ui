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
    request,
    session,
    url_for, abort)

from landoui.app import oidc
from landoui.forms import AltCommitMessageForm, TransplantRequestForm
from landoui.helpers import (
    get_phabricator_api_token, is_user_authenticated, set_last_local_referrer
)
from landoui.landoapi import LandoAPI, LandoAPIError
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

    # Build a mapping from phid to repository.
    repositories = {}
    for r in stack['repositories']:
        repositories[r['phid']] = r

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
    target_repo = None
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
        target_repo = repositories.get(revisions[series[0]]['repo_phid'])

    phids = set(revisions.keys())
    edges = set(Edge(child=e[0], parent=e[1]) for e in stack['edges'])
    order = sort_stack_topological(
        phids, edges, key=lambda x: int(revisions[x]['id'][1:])
    )
    drawing_width, drawing_rows = draw_stack_graph(phids, edges, order)

    if current_app.config.get("ENABLE_SEC_APPROVAL"):
        if "treat_as_secure" in request.args:
            # Override the default secure revision determination logic, treat the
            # revision we are viewing as if it were a secure revision for template
            # rendering purposes.  Useful for template testing and development where it
            # can be a pain to generate real secure revisions.
            use_sec_approval_workflow = True
        elif dryrun:
            secure_revision_phids = dryrun.get("secureRevisions", [])
            use_sec_approval_workflow = revision in secure_revision_phids
        else:
            use_sec_approval_workflow = False
    else:
        use_sec_approval_workflow = False

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
        use_sec_approval_workflow=use_sec_approval_workflow,
        target_repo=target_repo,
        errors=errors,
        form=form,
    )


@revisions.route(
    '/revisions/D<int:revision_id>/<diff_id>/', methods=('GET', 'POST')
)
@revisions.route('/revisions/D<int:revision_id>/')
def revisions_handler(revision_id, diff_id=None):
    # Redirect old revision page URL to stack page.
    return redirect(
        url_for('revisions.revision', revision_id=revision_id), code=301
    )


@revisions.route('/D<int:revision_id>/commit-message', methods=("POST",))
def alt_commit_message(revision_id):
    if not current_app.config.get("ENABLE_SEC_APPROVAL"):
        abort(404)

    form = AltCommitMessageForm()
    errors = []
    if form.is_submitted():
        if not is_user_authenticated():
            errors.append('You must be logged in to set an alternative commit message.')

        elif not form.validate():
            for _, field_errors in form.errors.items():
                errors.extend(field_errors)

    if errors:
        return "\n".join(errors), 400

    # FIXME: ensure the submitted revision is a secure revision!

    return "New commit message for revision {} (PHID {}) set to {}".format(
        revision_id,
        form.phid.data,
        form.alt_commit_message.data
    )
