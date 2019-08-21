# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import time
from copy import deepcopy
from unittest.mock import patch

import pytest

LANDO_API_REVISION = {
    "revisions": [
        {
            "repo_phid":
            "PHID-REPO-tk2tekowvewl4wfqh24m",
            "date_created":
            "2019-06-04T00:40:44+00:00",
            "diff": {
                "date_created": "2019-06-04T00:40:43+00:00",
                "date_modified": "2019-06-04T00:40:44+00:00",
                "phid": "PHID-DIFF-nbvuhc37tzdm4mj4ey7u",
                "id": 2,
                "author": {
                    "name": "Conduit Test User",
                    "email": "conduit@mozilla.bugs",
                },
            },
            "summary":
            "",
            "url":
            "http://phabricator.test/D1",
            "phid":
            "PHID-DREV-p4cpedtcru7sos24hc7h",
            "blocked_reason":
            "",
            "status": {
                "display": "Accepted",
                "value": "accepted",
                "closed": False,
            },
            "id":
            "D1",
            "reviewers": [
                {
                    "phid": "PHID-PROJ-vcgw2npz7ck6io7jdtwl",
                    "status": "accepted",
                    "for_other_diff": False,
                    "full_name": "sec-approval",
                    "identifier": "sec-approval",
                    "blocking_landing": False,
                },
                {
                    "phid": "PHID-USER-2sdofyo7e4vfyqolwxmp",
                    "status": "accepted",
                    "for_other_diff": False,
                    "full_name": "Conduit Reviewer",
                    "identifier": "ConduitReviewer",
                    "blocking_landing": False,
                },
            ],
            "is_secure":
            False,
            "author": {
                "phid": "PHID-USER-oqf26aifqpk7nzcvsy75",
                "username": "conduit",
                "real_name": "Conduit Test User",
            },
            "date_modified":
            "2019-06-13T15:04:33+00:00",
            "commit_message":
            "Bug 2 - test secure commits r=sec-approval,ConduitReviewer\n\nDifferential Revision: http://phabricator.test/D1",  # noqa
            "commit_message_title":
            "Bug 2 - test secure commits r=sec-approval,ConduitReviewer",
            "bug_id":
            2,
            "title":
            "test secure commits",
        }
    ],
    "landable_paths": [["PHID-DREV-p4cpedtcru7sos24hc7h"]],
    "edges": [],
    "repositories": [
        {
            "phid": "PHID-REPO-tk2tekowvewl4wfqh24m",
            "landing_supported": True,
            "url": "http://hg.test",
            "short_name": "test-repo",
        }
    ],
}


class LandoAPIDouble:
    """Returns canned responses for LandoAPI.request()"""

    default_stack_response = deepcopy(LANDO_API_REVISION)

    def __init__(self):
        self.stack_response = deepcopy(self.default_stack_response)

    def __call__(
        self, patch_object_self, http_method, operation, *args, **kwargs
    ):
        """A replacement for LandoAPI.request().

        Knows how to return canned responses for the various operations
        against Lando API necessary to render a page on the site.
        """
        # Mock Lando API operations.
        if operation.startswith("stacks"):
            # Mock response for "GET /stacks/D<int>" operation.
            return self.stack_response
        elif operation == "transplants":
            # Mock response for the "GET /transplants" operation.
            # Pretend there are not transplants in progress for the stack of
            # revisions.
            return {}
        elif operation == "transplants/dryrun":
            # Mock response for the "GET /transplants/dryrun" operation.
            # Pretend there are no landing warnings or blockers.
            return {}
        else:
            raise RuntimeError(
                "The API method for {} is not implemented by this stub".
                format(operation)
            )


@pytest.fixture(autouse=True)
def app_config(app):
    app.config["ENABLE_SEC_APPROVAL"] = True


@pytest.fixture(autouse=True)
def apidouble():
    """Patch lando-api to return stub responses."""
    with patch("landoui.landoapi.LandoAPI.request", autospec=True) as api:
        api.side_effect = LandoAPIDouble()
        yield api


@pytest.fixture
def authenticated_session(client, monkeypatch):
    """Simulate a session for a user who has authenticated with Auth0."""
    # We need to use the session_transaction() method to modify the session
    # in a way that affects both application code and template code sessions.
    #
    # If we only modify the session global then the global session object
    # will be modified but the template session object will be blank.
    #
    # Note: unfortunately the session object in the current process is still
    # blank so we can't test if landoui.helpers.is_user_authenticated() ==
    # True.
    with client.session_transaction() as session:
        session["id_token"] = "foo_id_token"
        session["access_token"] = "foo_access_token"
        session["userinfo"] = {"picture": ""}

        # These two values need to be present in the session for the OIDC
        # auth library to evaluate the session as fresh and authenticated.
        session["id_token_jwt"] = "foo_jwt"
        session["last_authenticated"] = time.time()


@pytest.fixture
def anonymous_session(client):
    """Simulate a session for an unauthenticated (anonymous) user."""
    # We need to use the session_transaction() method to modify the session
    # in a way that affects both application code and template code sessions.
    #
    # If we only modify the session global then the global session object
    # will be modified but the template session object will be blank.
    #
    # Note: unfortunately the session object in the current process is still
    # blank so we can't test if landoui.helpers.is_user_authenticated() ==
    # False.
    with client.session_transaction() as session:
        assert not session.keys()  # Check just to be sure.


def test_view_stack_not_logged_in(client, anonymous_session, apidouble):
    # Basic happy-path test for an anonymous user.
    rv = client.get("/D1/")
    assert rv.status_code == 200


def test_view_stack_logged_in(client, authenticated_session):
    # Basic happy-path test for a logged in user.
    rv = client.get("/D1/")
    assert rv.status_code == 200


def test_sec_approval_workflow_mark_hidden_if_revision_is_public(
    client, authenticated_session
):
    rv = client.get("/D1/")
    assert rv.status_code == 200
    assert (
        b"<!-- This revision is subject to the sec-approval workflow -->"
        not in rv.data
    )


def test_sec_approval_workflow_mark_shown_if_revision_is_secure(
    client, authenticated_session, apidouble
):
    apidouble.side_effect.stack_response["revisions"][0]["is_secure"] = True
    rv = client.get("/D1/")
    assert rv.status_code == 200
    assert (
        b"<!-- This revision is subject to the sec-approval workflow -->" in
        rv.data
    )


def test_sec_approval_workflow_mark_hidden_if_feature_flag_is_off(
    app, client, authenticated_session, apidouble
):
    app.config["ENABLE_SEC_APPROVAL"] = False
    apidouble.side_effect.stack_response["revisions"][0]["is_secure"] = True
    rv = client.get("/D1/")
    assert rv.status_code == 200
    assert (
        b"<!-- This revision is subject to the sec-approval workflow -->"
        not in rv.data
    )
