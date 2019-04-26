# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import time
from copy import deepcopy
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.usefixtures("app_config")


class LandoAPIDouble:
    """Returns canned responses for LandoAPI.request()"""

    # A fake lando-api response that contains the minimum data necessary to
    # render the lando front-page template.
    default_stack_response = {
        "edges": [],
        "landable_paths": [["PHID-DREV-phoo"]],
        "revisions": [
            {
                "phid": "PHID-DREV-phoo",
                "id": "D1",
                "diff": {
                    "id": 1,
                    "author": "Wobble"
                },
                "repo_phid": "PHID-REPO-repo",
                "status": {
                    "closed": False,
                    "display": "Needs Review",
                    "value": "needs-review",
                },
                "is_secure": False,
            }
        ],
        "repositories": [],
    }

    def __init__(self):
        self.stack_response = deepcopy(self.default_stack_response)

    def __call__(self, patched_object_self, operation, *args, **kwargs):
        """A replacement for LandoAPI.request().

        Knows how to return canned responses for the various operations
        against Lando API necessary to render a page on the site.
        """
        if operation.startswith("stacks"):
            return self.stack_response
        elif operation == "transplants":
            return {}
        elif operation == "transplants/dryrun":
            return {}
        else:
            raise RuntimeError(
                "The API method for {} is not implemented by this stub".
                format(operation)
            )


@pytest.fixture
def app_config(app):
    app.config["ENABLE_SEC_APPROVAL"] = True


@pytest.fixture
def apidouble():
    """Patch lando-api to return stub responses."""
    stub = LandoAPIDouble()
    with patch("landoui.landoapi.LandoAPI.request") as api:
        api.side_effect = stub
        yield stub


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


def test_view_stack_logged_in(client, authenticated_session, apidouble):
    # Basic happy-path test for a logged in user.
    rv = client.get("/D1/")
    assert rv.status_code == 200


def test_sec_approval_form_hidden_if_current_revision_is_public(
    client, authenticated_session, apidouble
):
    rv = client.get("/D1/")
    assert rv.status_code == 200
    assert b'id="altCommitMessageForm"' not in rv.data


def test_sec_approval_form_shown_if_current_revision_is_secure(
    client, authenticated_session, apidouble
):
    apidouble.stack_response["revisions"][0]["is_secure"] = True
    rv = client.get("/D1/")
    assert rv.status_code == 200
    assert b'id="altCommitMessageForm"' in rv.data


def test_submit_alt_commit_message(app, client, authenticated_session):
    # Disable CSRF protection so we can submit forms without tokens.
    app.config["WTF_CSRF_ENABLED"] = False

    formdata = {"phid": "PHID-DREV-phoo", "alt_commit_message": "s3cr3t"}
    rv = client.post(
        "/D1/commit-message", data=formdata, follow_redirects=True
    )

    assert rv.status_code == 200
    assert b"s3cr3t" in rv.data
