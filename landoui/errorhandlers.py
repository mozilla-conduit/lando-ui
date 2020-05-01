# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging

from flask import render_template

from landoui.sentry import sentry
from landoui.landoapi import (
    LandoAPICommunicationException,
    LandoAPIError,
    LandoAPIException,
)

logger = logging.getLogger(__name__)


class UIError(Exception):
    """An exception to be used to display an error page if not caught.

    Throw this exception when you want to inform the user of why something
    went wrong. A full error page will be shown and the user can then navigate
    to another part of the site.

    Attributes:
        title: The title of the problem to be shown on the error page.
        message: Details about the problem to be shown in the body of the page.
        status_code: The status code of the problem to be used in the http
            response of the error page. Defaults to 500.
    """

    def __init__(self, title, message, status_code=500):
        Exception.__init__(self, "%s: %s" % (title, message))
        self.title = title
        self.message = message
        self.status_code = status_code


class RevisionNotFound(Exception):
    """An exception for when a revision is required but not found.

    A custom error page for the case when a revision is not found will be
    displayed.

    Attributes:
        revision_id: The revision_id which could not be found.
        diff_id: The diff_id requested with the revision, if any.
    """

    def __init__(self, revision_id, diff_id="not specified"):
        message = (
            "Revision {revision_id} or Diff {diff_id} not found"
            "or permission denied.".format(revision_id=revision_id, diff_id=diff_id)
        )
        Exception.__init__(self, message)


def page_not_found(e):
    """Handler for generic 404 errors."""
    return (
        render_template(
            "errorhandlers/default_error.html",
            title="Page Not Found",
            message="The page you request could not be found.",
        ),
        404,
    )


def revision_not_found(e):
    """Handler for uncaught RevisionNotFound not found errors."""
    return render_template("errorhandlers/revisions_404.html"), 404


def ui_error(e):
    """Handler for all uncaught UIErrors."""
    return (
        render_template(
            "errorhandlers/default_error.html", title=e.title, message=e.message
        ),
        e.status_code,
    )


def unexpected_error(e):
    """Handler for all uncaught Exceptions."""

    logger.exception("unexpected error")
    sentry.captureException()

    return (
        render_template(
            "errorhandlers/default_error.html",
            title="Oops! Something went wrong.",
            message=(
                "Something just went wrong. Try again or tell the team at "
                "#lando on Matrix."
            ),
        ),
        500,
    )


def landoapi_communication(e):
    sentry.captureException()
    logger.exception("Uncaught communication exception with Lando API.")

    return (
        render_template(
            "errorhandlers/default_error.html",
            title="Could not Communicate with Lando API",
            message=(
                "There was an error when trying to communicate with "
                "Lando API. Please try your request again later."
            ),
        ),
        500,
    )


def landoapi_exception(e):
    sentry.captureException()
    logger.exception("Uncaught communication exception with Lando API.")

    return (
        render_template(
            "errorhandlers/default_error.html",
            title="Lando API returned an unexpected error",
            message=str(e),
        ),
        500,
    )


def register_error_handlers(app):
    """Function to register error handlers on the flask app."""
    app.register_error_handler(LandoAPICommunicationException, landoapi_communication)
    app.register_error_handler(LandoAPIError, landoapi_exception)
    app.register_error_handler(LandoAPIException, landoapi_exception)
    app.register_error_handler(RevisionNotFound, revision_not_found)
    app.register_error_handler(UIError, ui_error)
    app.register_error_handler(500, unexpected_error)
    app.register_error_handler(404, page_not_found)
