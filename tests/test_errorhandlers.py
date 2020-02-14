# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from landoui.errorhandlers import UIError, RevisionNotFound


def test_unknown_route_shows_default_404_page(client):
    response = client.get("/this_route_does_not_exist")
    assert response.status_code == 404
    assert b"Page Not Found" in response.get_data()


def test_revision_not_found_shows_revision_404_page(app, client):
    @app.route("/_tests/revisionnotfound")
    def bad_route():
        raise RevisionNotFound("D9000")

    response = client.get("/_tests/revisionnotfound")
    assert response.status_code == 404
    assert b"Revision/Diff Not Available" in response.get_data()


def test_ui_error_shows_uierror_page(app, client):
    @app.route("/_tests/uierror")
    def bad_route():
        raise UIError(
            title="Test Suite UI Error",
            message="This error must be in the test error page",
            status_code=405,
        )

    response = client.get("/_tests/uierror")
    assert response.status_code == 405
    assert b"Test Suite UI Error" in response.get_data()
    assert b"This error must be in the test error page" in response.get_data()


def test_unexpected_error_shows_default_500_page(app, client):
    # Disable the TESTING and DEBUG flags to allow exceptions to propagate
    # up to the flask error handlers.
    app.config["TESTING"] = False
    app.config["DEBUG"] = False

    @app.route("/_tests/bad_route")
    def bad_route():
        raise Exception("Unhandled exception")

    response = client.get("/_tests/bad_route")
    assert response.status_code == 500
    assert b"Oops! Something went wrong." in response.get_data()


def test_trailing_slash_gets_redirected(app, client):
    @app.route("/_tests/success/")
    def success():
        return "Success!"

    response = client.get("/_tests/success", follow_redirects=True)
    assert response.status_code == 200
    assert b"Success!" in response.get_data()
