# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from unittest.mock import patch

pytestmark = pytest.mark.usefixtures("app_config")

# A fake lando-api response that contains the minimum data necessary to render the
# lando front-page template.
STACK_RESPONSE = {
    "edges": [],
    "landable_paths": [["PHID-DREV-phoo"]],
    "revisions": [
        {
            "phid": "PHID-DREV-phoo",
            "id": "D1",
            "diff": {"id": 1, "author": "Wobble"},
            "repo_phid": "PHID-REPO-repo",
            "status": {
                "closed": False,
                "display": "Needs Review",
                "value": "needs-review",
            },
        }
    ],
    "repositories": [],
}


class StubLandoAPIRequest:
    """Stub for the LandoAPI object's .request() method.

    Meant to replace the real object's method using unittest.patch() or
    pytest monkeypatch.
    """

    def __init__(self, transplant_dryrun_response=None):
        """
        Args:
            transplant_dryrun_response: Optional response data to return from calls
                to the LandoAPI /transplants/dryrun operation.  Default: {}
        """
        self.transplant_dryrun_response = transplant_dryrun_response or {}

    def __call__(self, real_object_self, operation, *args, **kwargs):
        """A replacement for LandoAPI.request().

        Knows how to return canned responses for the various operations
        against Lando API necessary to render a page on the site.
        """
        if operation.startswith("stacks"):
            return STACK_RESPONSE
        elif operation == "transplants":
            return {}
        elif operation == "transplants/dryrun":
            return self.transplant_dryrun_response
        else:
            raise RuntimeError(
                "The API method for {} is not implemented by this stub".format(
                    operation
                )
            )


@pytest.fixture
def app_config(app):
    app.config["ENABLE_SEC_APPROVAL"] = True


@pytest.fixture
def authenticated_session(client):
    """Simulate a session for a user who has authenticated with Auth0."""
    # We need to use the session_transaction() method to modify the session
    # in a way that affects both application code and template code sessions.
    #
    # If we only modify the session global then the global session object will be
    # modified but the template session object will be blank.
    #
    # Note: unfortunately the session object in the current process is still blank
    # so we can't test if landoui.helpers.is_user_authenticated() == True.
    with client.session_transaction() as session:
        session["id_token"] = "foo_id_token"
        session["access_token"] = "foo_access_token"
        session["userinfo"] = {"picture": ""}


@pytest.fixture
def anonymous_session(client):
    """Simulate a session for an unauthenticated (anonymous) user."""
    # We need to use the session_transaction() method to modify the session
    # in a way that affects both application code and template code sessions.
    #
    # If we only modify the session global then the global session object will be
    # modified but the template session object will be blank.
    #
    # Note: unfortunately the session object in the current process is still blank
    # so we can't test if landoui.helpers.is_user_authenticated() == False.
    with client.session_transaction() as session:
        assert not session.keys()  # Check just to be sure.


def test_view_stack_not_logged_in(client, anonymous_session):
    # Basic happy-path test for an anonymous user.
    with patch("landoui.landoapi.LandoAPI.request") as api:
        api.side_effect = StubLandoAPIRequest()

        rv = client.get("/D1/")

        assert rv.status_code == 200


def test_view_stack_logged_in(client, authenticated_session):
    # Basic happy-path test for a logged in user.
    with patch("landoui.landoapi.LandoAPI.request") as api:
        api.side_effect = StubLandoAPIRequest()

        rv = client.get("/D1/")

        assert rv.status_code == 200


def test_sec_approval_form_shown_if_path_has_force_feature_flag(
    client, authenticated_session
):
    with patch("landoui.landoapi.LandoAPI.request") as api:
        api.side_effect = StubLandoAPIRequest()

        rv = client.get("/D1/?treat_as_secure")

        assert rv.status_code == 200
        assert b'id="altCommitMessageForm"' in rv.data


def test_sec_approval_form_hidden_if_no_secure_revisions_in_stack(
    client, authenticated_session
):
    with patch("landoui.landoapi.LandoAPI.request") as api:
        api.side_effect = StubLandoAPIRequest()

        rv = client.get("/D1/")

        assert rv.status_code == 200
        assert b'id="altCommitMessageForm"' not in rv.data


def test_sec_approval_form_shown_if_secure_revisions_in_stack(
    client, authenticated_session
):
    transplant_dryrun_response = {"secureRevisions": ["PHID-DREV-phoo"]}

    with patch("landoui.landoapi.LandoAPI.request") as api:
        api.side_effect = StubLandoAPIRequest(transplant_dryrun_response)

        rv = client.get("/D1/")

        assert rv.status_code == 200
        assert b'id="altCommitMessageForm"' in rv.data


def test_submit_alt_commit_messages(app, client, authenticated_session):
    revision_phid = "PHID-DREV-phoo"
    transplant_dryrun_response = {"secureRevisions": [revision_phid]}

    # Disable CSRF protection so we can submit forms without tokens.
    app.config["WTF_CSRF_ENABLED"] = False

    with patch("landoui.landoapi.LandoAPI.request") as api:
        api.side_effect = StubLandoAPIRequest(transplant_dryrun_response)

        formdata = {
            "phid": revision_phid,
            "alt_commit_message": "s3cr3t",
        }
        rv = client.post("/D1/commit-message", data=formdata, follow_redirects=True)

        assert rv.status_code == 200
        assert b's3cr3t' in rv.data
