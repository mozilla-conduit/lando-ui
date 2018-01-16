# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# yapf: disable
# flake8: noqa

LANDO_API_RESPONSE = {
    "status": 1,
    "status_name": "Needs Revision",
    "title": "My test diff 1",
    "summary": "Summary 1",
    "test_plan": "Test Plan 1",
    "commit_message_title": "Bug 1 - My test diff 1 r=review_bot",
    "commit_message": (
        "Bug 1 - My test diff 1 r=review_bot\n\n"
        "Summary 1\n\nDifferential Revision: http://phabricator.test/D1"
    ),
    "url": "http://phabricator.test/D1",
    "date_created": 1495638270,
    "date_modified": 1496239141,
    "id": 'D1',
    "parent_revisions": [],
    "bug_id": 1,
    "phid": "PHID-DREV-1",
    "diff": {
        "date_created": 1496175380,
        "date_modified": 1496175382,
        "id": 1,
        "revision_id": 'D1',
        "vcs_base_revision": "39d5cc0fda5e16c49a59d29d4ca186a5534cc88b",
        "authors": [
            {"email": "mcote@mozilla.example", "name": "Mark Cote"},
            {"email": "glob@mozilla.example", "name": "Byron Jones"}
        ],
    },
    "latest_diff_id": 1,
    "author": {
        "image_url": "https://d2kb8dptaglwte.cloudfront.net/file/data/oywgsrq6rtv5rdfbjvdv/PHID-FILE-632bsum6ksnpu77kymbq/alphanumeric_lato-dark_I.png-_5e622c-255%2C255%2C255%2C0.4.png", # noqa
        "phid": "PHID-USER-imaduemeadmin",
        "real_name": "Israel Madueme",
        "url": "http://phabricator.test/p/imadueme_admin/",
        "username": "imadueme_admin"
    },
    "repo": {
        "full_name": "rMOZILLACENTRAL mozilla-central",
        "phid": "PHID-REPO-mozillacentral",
        "short_name": "rMOZILLACENTRAL",
        "url": "http://phabricator.test/source/mozilla-central/"
    },
    'reviewers': [
        {
            'phid': 'PHID-USER-review_bot',
            'is_blocking': False,
            'real_name': 'review_bot Name',
            'status': 'added',
            'username': 'review_bot'
        }
    ]
}

LANDO_API_LANDINGS_RESPONSE = []
