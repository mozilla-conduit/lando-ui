# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import datetime
import logging
import re
import urllib.parse

from flask import Blueprint, current_app, escape
from landoui.forms import UserSettingsForm

from landoui import helpers

FAQ_URL = "https://wiki.mozilla.org/Phabricator/FAQ#Lando"
SEC_BUG_WIKI = "https://wiki.mozilla.org/Security/Bug_Approval_Process"

logger = logging.getLogger(__name__)
template_helpers = Blueprint("template_helpers", __name__)


@template_helpers.app_template_global()
def is_user_authenticated():
    return helpers.is_user_authenticated()


@template_helpers.app_template_global()
def new_settings_form():
    return UserSettingsForm()


@template_helpers.app_template_filter()
def escape_html(text):
    return escape(text)


@template_helpers.app_template_global()
def calculate_duration(start, end=None):
    """Calculates the duration between the two iso8061 timestamps.

    If end is None then the current time in UTC will be used.
    Returns a dict with the minutes and seconds as integers.
    """
    if not end:
        utc_tz = datetime.timezone.utc
        end = datetime.datetime.utcnow().replace(tzinfo=utc_tz).isoformat()

    # Work around for ':' in timezone until we upgrade to Python 3.7.
    # https://bugs.python.org/issue24954
    start = start[:-3] + start[-2:]
    end = end[:-3] + end[-2:]

    time_start = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S.%f%z")
    time_end = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S.%f%z")
    elapsedTime = time_end - time_start
    result = divmod(elapsedTime.total_seconds(), 60)
    return {"minutes": int(result[0]), "seconds": int(result[1])}


@template_helpers.app_template_filter()
def tostatusbadgeclass(status):
    mapping = {
        "aborted": "Badge Badge--negative",
        "submitted": "Badge Badge--warning",
        "in_progress": "Badge Badge--warning",
        "landed": "Badge Badge--positive",
        "failed": "Badge Badge--negative",
    }
    return mapping.get(status["status"].lower(), "Badge Badge--negative")


@template_helpers.app_template_filter()
def reviewer_to_status_badge_class(reviewer):
    return {
        # status: (current_diff, for_other_diff),
        "accepted": ("Badge Badge--positive", "Badge Badge--neutral"),
        "rejected": ("Badge Badge--negative", "Badge Badge--warning"),
        "added": ("Badge", "Badge"),
        "blocking": ("Badge", "Badge"),
        "resigned": ("Badge", "Badge"),
    }.get(reviewer["status"], ("Badge Badge--warning", "Badge Badge--warning"))[
        1 if reviewer["for_other_diff"] else 0
    ]


@template_helpers.app_template_filter()
def reviewer_to_action_text(reviewer):
    options = {
        # status: (current_diff, for_other_diff),
        "accepted": ("accepted", "accepted a prior diff"),
        "rejected": ("requested changes", "requested changes to a prior diff"),
        "added": ("to review", "to review"),
        "blocking": ("must review", "must review"),
        "resigned": ("resigned", "resigned"),
    }.get(reviewer["status"], ("UNKNOWN STATE", "UNKNOWN STATE"))
    return options[1 if reviewer["for_other_diff"] else 0]


@template_helpers.app_template_filter()
def revision_status_to_badge_class(status):
    return {
        "abandoned": "Badge",
        "accepted": "Badge Badge--positive",
        "changes-planned": "Badge Badge--neutral",
        "published": "Badge",
        "needs-review": "Badge Badge--warning",
        "needs-revision": "Badge Badge--negative",
        "draft": "Badge Badge--neutral",
    }.get(status, "Badge Badge--warning")


@template_helpers.app_template_filter()
def tostatusbadgename(status):
    mapping = {
        "aborted": "Aborted",
        "submitted": "Landing queued",
        "in_progress": "In progress",
        "landed": "Successfully landed",
        "failed": "Failed to land",
    }
    return mapping.get(status["status"].lower(), status["status"].capitalize())


@template_helpers.app_template_filter()
def avatar_url(url):
    # If a user doesn't have a gravatar image for their auth0 email address,
    # gravatar uses auth0's provided default which redirects to
    # *.wp.com/cdn.auth0.com/. Instead of whitelisting this in our CSP,
    # here, we opt into a default generated image provided by gravatar.
    try:
        parsed_url = urllib.parse.urlsplit(url)
        if not parsed_url.netloc:
            raise ValueError("Avatar URLs should not be relative")
    except (AttributeError, ValueError):
        logger.debug("Invalid avatar url provided", extra={"url": url})
        return ""

    if parsed_url.netloc in ("s.gravatar.com", "www.gravatar.com"):
        query = urllib.parse.parse_qs(parsed_url.query)
        query["d"] = "identicon"
        parsed_url = (
            parsed_url[:3]
            + (urllib.parse.urlencode(query, doseq=True),)
            + parsed_url[4:]
        )

    return urllib.parse.urlunsplit(parsed_url)


@template_helpers.app_template_filter()
def linkify_bug_numbers(text):
    search = r"(?=\b)(Bug (\d+))(?=\b)"
    replace = r'<a href="{bmo_url}/show_bug.cgi?id=\g<2>">\g<1></a>'.format(
        bmo_url=current_app.config["BUGZILLA_URL"]
    )
    return re.sub(search, replace, str(text), flags=re.IGNORECASE)


@template_helpers.app_template_filter()
def linkify_revision_urls(text):
    search = (
        r"(?=\b)(" + re.escape(current_app.config["PHABRICATOR_URL"]) + r"/D\d+)(?=\b)"
    )
    replace = r'<a href="\g<1>">\g<1></a>'
    return re.sub(search, replace, str(text), flags=re.IGNORECASE)


@template_helpers.app_template_filter()
def linkify_transplant_details(text, transplant):
    # The transplant result is not always guaranteed to be a commit id. It
    # can be a message saying that the landing was queued and will land later.
    if transplant["status"].lower() != "landed":
        return text

    commit_id = transplant["details"]
    search = r"(?=\b)(" + re.escape(commit_id) + r")(?=\b)"
    replace = r'<a href="{repo_url}/rev/\g<1>">{repo_url}/rev/\g<1></a>'.format(
        repo_url=transplant["repository_url"]
    )
    return re.sub(search, replace, str(text))  # This is case sensitive


@template_helpers.app_template_filter()
def linkify_faq(text):
    search = r"\b(FAQ)\b"
    replace = r'<a href="{faq_url}">\g<1></a>'.format(faq_url=FAQ_URL)
    return re.sub(search, replace, str(text), flags=re.IGNORECASE)


@template_helpers.app_template_filter()
def linkify_sec_bug_wiki(text):
    search = r"\b(Security Bug Approval Process)\b"
    replace = r'<a href="{wiki_url}">\g<1></a>'.format(wiki_url=SEC_BUG_WIKI)
    return re.sub(search, replace, str(text), flags=re.IGNORECASE)


@template_helpers.app_template_filter()
def bug_url(text):
    return "{bmo_url}/show_bug.cgi?id={bug_number}".format(
        bmo_url=current_app.config["BUGZILLA_URL"], bug_number=text
    )


@template_helpers.app_template_filter()
def revision_url(text, diff_id=None):
    url = "{phab_url}/{revision_id}".format(
        phab_url=current_app.config["PHABRICATOR_URL"], revision_id=text
    )
    if diff_id is not None and diff_id != "":
        url = "{revision_url}?id={diff_id}".format(revision_url=url, diff_id=diff_id)

    return url


@template_helpers.app_template_filter()
def repo_path(repo_url):
    """Returns the path of a repository url without the leading slash.

    If the result would be empty, the full URL is returned.
    """
    if not repo_url:
        return ""
    repo = urllib.parse.urlsplit(repo_url).path.strip().strip("/")
    return repo if repo else repo_url


GRAPH_DRAWING_COL_WIDTH = 14
GRAPH_DRAWING_HEIGHT = 44
GRAPH_DRAWING_COLORS = [
    "#cc0000",
    "#cc0099",
    "#6600cc",
    "#0033cc",
    "#00cccc",
    "#00cc33",
    "#66cc00",
    "#cc9900",
]


@template_helpers.app_template_filter()
def graph_width(cols):
    return GRAPH_DRAWING_COL_WIDTH * cols


@template_helpers.app_template_global()
def graph_height():
    return GRAPH_DRAWING_HEIGHT


@template_helpers.app_template_filter()
def graph_x_pos(col):
    return (GRAPH_DRAWING_COL_WIDTH * col) + (GRAPH_DRAWING_COL_WIDTH / 2)


@template_helpers.app_template_filter()
def graph_color(col):
    return GRAPH_DRAWING_COLORS[col % len(GRAPH_DRAWING_COLORS)]


@template_helpers.app_template_filter()
def graph_above_path(col, above):
    commands = [
        "M {x} {y}".format(x=graph_x_pos(above), y=0),
        "C {x1} {y1}, {x2} {y2}, {x} {y}".format(
            x1=graph_x_pos(above),
            y1=GRAPH_DRAWING_HEIGHT / 4,
            x2=graph_x_pos(col),
            y2=GRAPH_DRAWING_HEIGHT / 4,
            x=graph_x_pos(col),
            y=GRAPH_DRAWING_HEIGHT / 2,
        ),
    ]
    return " ".join(commands)


@template_helpers.app_template_filter()
def graph_below_path(col, below):
    commands = [
        "M {x} {y}".format(x=graph_x_pos(col), y=GRAPH_DRAWING_HEIGHT / 2),
        "C {x1} {y1}, {x2} {y2}, {x} {y}".format(
            x1=graph_x_pos(col),
            y1=3 * GRAPH_DRAWING_HEIGHT / 4,
            x2=graph_x_pos(below),
            y2=3 * GRAPH_DRAWING_HEIGHT / 4,
            x=graph_x_pos(below),
            y=GRAPH_DRAWING_HEIGHT,
        ),
    ]
    return " ".join(commands)


@template_helpers.app_template_filter()
def message_type_to_notification_class(flash_message_category):
    """Map a Flask flash message category to a Bulma notification CSS class.

    See https://bulma.io/documentation/elements/notification/ for the list of
    Bulma notification states.
    """
    return {"info": "is-info", "success": "is-success", "warning": "is-warning",}.get(
        flash_message_category, "is-info"
    )
