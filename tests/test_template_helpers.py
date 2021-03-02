# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import urllib.parse

import pytest

from landoui.template_helpers import (
    avatar_url,
    linkify_bug_numbers,
    linkify_revision_urls,
    linkify_faq,
    linkify_sec_bug_docs,
    repo_path,
    calculate_duration,
    revision_url,
)


@pytest.mark.parametrize(
    "input_url,output_url",
    [
        (
            "https://lh3.googleusercontent.com/-ABCDef/123/photo.jpg",
            "https://lh3.googleusercontent.com/-ABCDef/123/photo.jpg",
        ),
        (
            "https://s.gravatar.com/avatar/9b665?s=480&r=pg&d=https%3A%2F%2Fcdn.auth0.com%2Favatars%2Fcs.png",  # noqa
            "https://s.gravatar.com/avatar/9b665?s=480&r=pg&d=identicon",
        ),
        (
            "https://s.gravatar.com/avatar/123b",
            "https://s.gravatar.com/avatar/123b?d=identicon",
        ),
        (
            "//www.gravatar.com/avatar/123b?s=480&r=pg&d=robohash",
            "//www.gravatar.com/avatar/123b?s=480&r=pg&d=identicon",
        ),
        ("/relative_path_only", ""),
        ("1 invalid url", ""),
        (9000, ""),
    ],
)
def test_avatar_url(input_url, output_url):
    # Query params are not guaranteed to be in the same order, so
    # we cannot do string comparison of the URLs.
    expected = urllib.parse.urlparse(output_url)
    actual = urllib.parse.urlparse(avatar_url(input_url))
    expected_qs = urllib.parse.parse_qs(expected.query)
    actual_qs = urllib.parse.parse_qs(actual.query)

    for argument in expected_qs:
        assert expected_qs[argument] == actual_qs[argument]

    assert (expected.scheme, expected.netloc, expected.path) == (
        actual.scheme,
        actual.netloc,
        actual.path,
    )


@pytest.mark.parametrize(
    "input_text,output_text",
    [
        ("Bug 123", '<a href="http://bmo.test/show_bug.cgi?id=123">Bug 123</a>'),
        ("bug 123", '<a href="http://bmo.test/show_bug.cgi?id=123">bug 123</a>'),
        (
            "Testing Bug 1413384 word boundaries",
            (
                'Testing <a href="http://bmo.test/show_bug.cgi?id=1413384">'
                "Bug 1413384</a> word boundaries"
            ),
        ),
        (
            "Bug 123 - commit title. r=test\n\nCommit message Bug 456",
            (
                '<a href="http://bmo.test/show_bug.cgi?id=123">Bug 123</a> - '
                "commit title. r=test\n\nCommit message "
                '<a href="http://bmo.test/show_bug.cgi?id=456">Bug 456</a>'
            ),
        ),
        ("A message with no bug number", "A message with no bug number"),
    ],
)
def test_linkify_bug_numbers(app, input_text, output_text):
    assert output_text == linkify_bug_numbers(input_text)


@pytest.mark.parametrize(
    "input_text,output_text",
    [
        (
            "http://phabricator.test/D123",
            (
                '<a href="http://phabricator.test/D123">'
                "http://phabricator.test/D123</a>"
            ),
        ),
        (
            "word http://phabricator.test/D201525 boundaries",
            (
                'word <a href="http://phabricator.test/D201525">'
                "http://phabricator.test/D201525</a> boundaries"
            ),
        ),
        (
            (
                "multiple http://phabricator.test/D123\n"
                "revisions http://phabricator.test/D456"
            ),
            (
                'multiple <a href="http://phabricator.test/D123">'
                "http://phabricator.test/D123</a>\nrevisions "
                '<a href="http://phabricator.test/D456">'
                "http://phabricator.test/D456</a>"
            ),
        ),
        (
            "No revision example: http://phabricator.test/herald/",
            "No revision example: http://phabricator.test/herald/",
        ),
    ],
)
def test_linkify_revision_urls(app, input_text, output_text):
    assert output_text == linkify_revision_urls(input_text)


@pytest.mark.parametrize(
    "input_text,output_text",
    [
        ("faq", '<a href="https://wiki.mozilla.org/Phabricator/FAQ#Lando">faq</a>'),
        ("FAQ", '<a href="https://wiki.mozilla.org/Phabricator/FAQ#Lando">FAQ</a>'),
        (
            "faqual message that should not be linked",
            "faqual message that should not be linked",
        ),
    ],
)
def test_linkify_faq(app, input_text, output_text):
    assert output_text == linkify_faq(input_text)


@pytest.mark.parametrize(
    "input_text,output_text",
    [
        (
            "security bug approval process",
            '<a href="https://firefox-source-docs.mozilla.org/bug-mgmt/processes/security-approval.html">security bug approval process</a>',  # noqa
        ),
        (
            "Security Bug Approval Process",
            '<a href="https://firefox-source-docs.mozilla.org/bug-mgmt/processes/security-approval.html">Security Bug Approval Process</a>',  # noqa
        ),
        (
            "security bug processes being used in a normal sentence",
            "security bug processes being used in a normal sentence",
        ),
    ],
)
def test_linkify_sec_bug_docs(app, input_text, output_text):
    assert output_text == linkify_sec_bug_docs(input_text)


@pytest.mark.parametrize(
    "repo_url,path",
    [
        (
            "https://hg.mozilla.org/automation/phabricator-qa-stage",
            "automation/phabricator-qa-stage",
        ),
        ("https://hg.mozilla.org/comm-central/", "comm-central"),
        ("http://hg.test", "http://hg.test"),
        (None, ""),
    ],
)
def test_repo_path(app, repo_url, path):
    assert path == repo_path(repo_url)


@pytest.mark.parametrize(
    "start,end,duration",
    [
        (
            "2019-10-08T06:42:12.000000+00:00",
            "2019-10-08T06:58:32.000000+00:00",
            {"minutes": 16, "seconds": 20},
        ),
        (
            "2019-10-10T12:42:34.012340+00:00",
            "2019-10-10T12:42:41.045670+00:00",
            {"minutes": 0, "seconds": 7},
        ),
    ],
)
def test_calculate_duration(app, start, end, duration):
    assert duration == calculate_duration(start, end)


def test_revision_url__integer(app):
    revision_id = 1234
    expected_result = "http://phabricator.test/D1234"
    actual_result = revision_url(revision_id)
    assert expected_result == actual_result


def test_revision_url__prepended_string(app):
    revision_id = "D1234"
    expected_result = "http://phabricator.test/D1234"
    actual_result = revision_url(revision_id)
    assert expected_result == actual_result


def test_revision_url__string(app):
    revision_id = "1234"
    expected_result = "http://phabricator.test/D1234"
    actual_result = revision_url(revision_id)
    assert expected_result == actual_result


def test_revision_url__general_case_with_diff(app):
    revision_id = 123
    diff_id = 456
    expected_result = "http://phabricator.test/D123?id=456"
    actual_result = revision_url(revision_id, diff_id)
    assert expected_result == actual_result
