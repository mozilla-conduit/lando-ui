# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import functools
import json
import logging

from itertools import (
    chain,
)
from typing import (
    Callable,
    Optional,
)

from flask import (
    abort,
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from landoui.app import oidc
from landoui.forms import (
    SecApprovalRequestForm,
    TransplantRequestForm,
    UpliftRequestForm,
)
from landoui.helpers import (
    get_phabricator_api_token,
    is_user_authenticated,
    set_last_local_referrer,
)
from landoui.landoapi import (
    LandoAPI,
    LandoAPICommunicationException,
    LandoAPIError,
)
from landoui.errorhandlers import RevisionNotFound
from landoui.stacks import draw_stack_graph, Edge, sort_stack_topological

logger = logging.getLogger(__name__)

revisions = Blueprint("revisions", __name__)
revisions.before_request(set_last_local_referrer)


def oidc_auth_optional(f) -> Callable:
    """Decorator that runs auth only if the user is logged in."""
    no_auth_f = f
    auth_f = oidc.oidc_auth("AUTH0")(f)

    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not is_user_authenticated():
            handler = no_auth_f
        else:
            handler = auth_f

        return handler(*args, **kwargs)

    return wrapped


def annotate_sec_approval_workflow_info(revisions: dict[str, dict]):
    """Annotate a dict of revisions with sec-approval workflow information.

    See https://firefox-source-docs.mozilla.org/bug-mgmt/processes/security-approval.html # noqa: E501

    Args:
        revisions: A dict of (phid, revision_data) items. The dict will have
            new keys added to it by this function.
    """
    for revision in revisions.values():
        if current_app.config.get("ENABLE_SEC_APPROVAL"):
            should_use_workflow = revision.get("is_secure", False)
        else:
            should_use_workflow = False
        revision["should_use_sec_approval_workflow"] = should_use_workflow


def get_uplift_repos(api: LandoAPI) -> list[tuple[str, str]]:
    """Return the set of uplift repositories as a list of `(name, value)` tuples."""
    uplift_repos = api.request("GET", "uplift")
    return [(repo, repo) for repo in uplift_repos["repos"]]


@revisions.route("/uplift/", methods=("POST",))
@oidc_auth_optional
def uplift():
    """Process the uplift request WTForms submission."""
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=get_phabricator_api_token(),
    )
    uplift_request_form = UpliftRequestForm()

    # Get the list of available uplift repos and populate the form with it.
    uplift_request_form.repository.choices = get_uplift_repos(api)

    if not uplift_request_form.is_submitted():
        return jsonify(errors=["Uplift request form not submitted."]), 401

    if not is_user_authenticated():
        return jsonify(errors=["You must be logged in to request an uplift"]), 401

    if not uplift_request_form.validate():
        errors = list(chain(*uplift_request_form.errors.values()))
        return jsonify(errors=errors), 400

    try:
        revision_id = uplift_request_form.revision_id.data
        repository = uplift_request_form.repository.data
    except json.JSONDecodeError as exc:
        raise LandoAPICommunicationException(
            "Landing path could not be decoded as JSON"
        ) from exc

    try:
        response = api.request(
            "POST",
            "uplift",
            require_auth0=True,
            json={
                "revision_id": revision_id,
                "repository": repository,
            },
        )
    except LandoAPIError as e:
        if not e.detail:
            raise e

        return jsonify(errors=[e.detail]), e.status_code

    # Redirect to the tip revision's URL.
    # TODO add js for auto-opening the uplift request Phabricator form.
    tip_differential = response["tip_differential"]["url"]
    return redirect(tip_differential)


@revisions.route("/D<int:revision_id>/", methods=("GET", "POST"))
@oidc_auth_optional
def revision(revision_id: int):
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=get_phabricator_api_token(),
    )

    form = TransplantRequestForm()
    sec_approval_form = SecApprovalRequestForm()
    uplift_request_form = UpliftRequestForm()

    # Get the list of available uplift repos and populate the form with it.
    uplift_request_form.repository.choices = get_uplift_repos(api)
    uplift_request_form.revision_id.data = revision_id

    errors = []
    if form.is_submitted():
        if not is_user_authenticated():
            errors.append("You must be logged in to request a landing")

        elif not form.validate():
            for _, field_errors in form.errors.items():
                errors.extend(field_errors)

        else:
            try:
                api.request(
                    "POST",
                    "transplants",
                    require_auth0=True,
                    json={
                        "landing_path": json.loads(form.landing_path.data),
                        "confirmation_token": form.confirmation_token.data,
                        "flags": json.loads(form.flags.data),
                    },
                )
                # We don't actually need any of the data from the
                # the submission. As long as an exception wasn't
                # raised we're successful.
                return redirect(url_for("revisions.revision", revision_id=revision_id))
            except LandoAPIError as e:
                if not e.detail:
                    raise

                errors.append(e.detail)

    # Request the entire stack.
    try:
        stack = api.request("GET", "stacks/D{}".format(revision_id))
    except LandoAPIError as e:
        if e.status_code == 404:
            raise RevisionNotFound(revision_id)
        else:
            raise

    # Build a mapping from phid to revision and identify
    # the data for the revision used to load this page.
    revision = None
    revisions = {}
    for r in stack["revisions"]:
        revisions[r["phid"]] = r
        if r["id"] == "D{}".format(revision_id):
            revision = r["phid"]

    # Build a mapping from phid to repository.
    repositories = {}
    for r in stack["repositories"]:
        repositories[r["phid"]] = r

    # Request all previous transplants for the stack.
    transplants = api.request(
        "GET", "transplants", params={"stack_revision_id": "D{}".format(revision_id)}
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
    for p in stack["landable_paths"]:
        for phid in p:
            landable.add(phid)

        try:
            series = p[: p.index(revision) + 1]
        except ValueError:
            pass

    dryrun = None
    target_repo = None
    if series and is_user_authenticated():
        landing_path = [
            {
                "revision_id": revisions[phid]["id"],
                "diff_id": revisions[phid]["diff"]["id"],
            }
            for phid in series
        ]
        landing_path_json = json.dumps(landing_path)
        form.landing_path.data = landing_path_json

        dryrun = api.request(
            "POST",
            "transplants/dryrun",
            require_auth0=True,
            json={"landing_path": landing_path},
        )
        form.confirmation_token.data = dryrun.get("confirmation_token")

        series = list(reversed(series))
        target_repo = repositories.get(revisions[series[0]]["repo_phid"])

    phids = set(revisions.keys())
    edges = set(Edge(child=e[0], parent=e[1]) for e in stack["edges"])
    order = sort_stack_topological(
        phids, edges, key=lambda x: int(revisions[x]["id"][1:])
    )
    drawing_width, drawing_rows = draw_stack_graph(phids, edges, order)

    annotate_sec_approval_workflow_info(revisions)

    # Are we showing the "sec-approval request submitted" dialog?
    # If we are then fill in its values.
    submitted_revision = request.args.get("show_approval_success")
    submitted_rev_url = None
    if submitted_revision:
        for rev in revisions.values():
            if rev["id"] == submitted_revision:
                submitted_rev_url = rev["url"]
                break

    # Current implementation requires that all commits have the flags appended.
    # This may change in the future. What we do here is:
    # - if all commits have the flag, then disable the checkbox
    # - if any commits do not have the flag, then enable the checkbox

    if target_repo:
        existing_flags = {f[0]: False for f in target_repo["commit_flags"]}
        for flag in existing_flags:
            existing_flags[flag] = all(
                flag in r["commit_message"] for r in revisions.values()
            )
    else:
        existing_flags = {}

    return render_template(
        "stack/stack.html",
        revision_id="D{}".format(revision_id),
        series=series,
        landable=landable,
        dryrun=dryrun,
        stack=stack,
        rows=list(zip(reversed(order), reversed(drawing_rows))),
        drawing_width=drawing_width,
        transplants=transplants,
        revisions=revisions,
        revision_phid=revision,
        sec_approval_form=sec_approval_form,
        submitted_rev_url=submitted_rev_url,
        target_repo=target_repo,
        errors=errors,
        form=form,
        flags=target_repo["commit_flags"] if target_repo else [],
        existing_flags=existing_flags,
        uplift_request_form=uplift_request_form,
    )


@revisions.route("/revisions/D<int:revision_id>/<diff_id>/", methods=("GET", "POST"))
@revisions.route("/revisions/D<int:revision_id>/")
def revisions_handler(revision_id: int, diff_id: Optional[str] = None):
    # Redirect old revision page URL to stack page.
    return redirect(url_for("revisions.revision", revision_id=revision_id), code=301)


@revisions.route("/request-sec-approval", methods=("POST",))
def sec_approval_request_handler():
    if not current_app.config.get("ENABLE_SEC_APPROVAL"):
        abort(404)

    if not is_user_authenticated():
        errors = make_form_error("You must be logged in to request sec-approval")
        return jsonify(errors=errors), 401

    token = get_phabricator_api_token()
    if not token:
        # The user has not set their API Token. Lando API will return an
        # error if it is missing.
        errors = make_form_error(
            "You must set your Phabricator API token in the Lando User "
            "Settings to request sec-approval"
        )
        return jsonify(errors=errors), 400

    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )

    form = SecApprovalRequestForm()

    if not form.validate():
        return jsonify(errors=form.errors), 400
    else:
        logger.info(
            "sec-approval requested", extra={"revision_id": form.revision_id.data}
        )

        # NOTE: We let errors in the upstream service get turned into
        # exceptions and bubble up to the application's default exception
        # handler. It will generate a HTTP 500 for the UI to handle.
        api.request(
            "POST",
            "requestSecApproval",
            require_auth0=True,
            json={
                "revision_id": form.revision_id.data,
                "sanitized_message": form.new_message.data,
            },
        )

    return jsonify({})


@revisions.route("/landing_jobs/<int:landing_job_id>", methods=("PUT",))
def update_landing_job(landing_job_id: int):
    if not is_user_authenticated():
        errors = make_form_error("You must be logged in to update a landing job.")
        return jsonify(errors=errors), 401

    token = get_phabricator_api_token()
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )

    try:
        data = api.request(
            "PUT",
            f"landing_jobs/{landing_job_id}",
            require_auth0=True,
            json=request.get_json(),
        )
    except LandoAPIError as e:
        return e.response, e.response["status"]
    return data


def make_form_error(message: str) -> dict[str, list[str]]:
    """Turn a string into an error that looks like a WTForm validation error.

    This can be used to generate one-off errors, like auth errors, that need
    to be displayed in the same space as WTForm validation errors.
    """
    # WTForm errors are stored in a dict. Keys are the field names, values are
    # a list of errors for that field.
    return {"Error": [message]}
