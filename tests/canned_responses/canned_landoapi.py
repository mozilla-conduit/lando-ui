# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# yapf: disable
# flake8: noqa

GET_REVISION_DEFAULT = {
    'status': 1,
    'status_name': 'Needs Revision',
    'title': 'My test diff 1',
    'summary': 'Summary 1',
    'test_plan': 'Test Plan 1',
    'commit_message_title': 'Bug 1 - My test diff 1 r=review_bot',
    'commit_message': (
        'Bug 1 - My test diff 1 r=review_bot\n\n'
        'Summary 1\n\nDifferential Revision: http://phabricator.test/D1'
    ),
    'url': 'http://phabricator.test/D1',
    'date_created': 1495638270,
    'date_modified': 1496239141,
    'id': 'D1',
    'parent_revisions': [],
    'bug_id': 1,
    'phid': 'PHID-DREV-1',
    'diff': {
        'date_created': 1496175380,
        'date_modified': 1496175382,
        'id': 1,
        'revision_id': 'D1',
        'vcs_base_revision': '39d5cc0fda5e16c49a59d29d4ca186a5534cc88b',
        'authors': [
            {'email': 'testuser@mozilla.example', 'name': 'Test User'},
            {'email': 'testuser@mozilla.example', 'name': 'Other User'}
        ],
    },
    'latest_diff_id': 1,
    'author': {
        'image_url': 'https://test.cloudfront.example/file/data/testuser.png', # noqa
        'phid': 'PHID-USER-testuser',
        'real_name': 'Test User',
        'url': 'http://phabricator.test/p/test_user/',
        'username': 'test_user'
    },
    'repo': {
        'full_name': 'rMOZILLACENTRAL mozilla-central',
        'phid': 'PHID-REPO-mozillacentral',
        'short_name': 'rMOZILLACENTRAL',
        'url': 'http://phabricator.test/source/mozilla-central/'
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


GET_REVISION_NOT_FOUND = {
    'detail': 'The requested revision does not exist',
    'status': 404,
    'title': 'Revision not found',
    'type': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404'
}


GET_LANDINGS_DEFAULT = [
    {
        'active_diff_id': 1,
        'created_at': '2018-02-09T20:48:20.293139',
        'diff_id': 1,
        'error_msg': '',
        'id': 1,
        'request_id': 100,
        'requester_email': 'testuser@mozilla.example',
        'result': '',
        'revision_id': 'D1',
        'status': 'submitted',
        'tree': 'autoland',
        'updated_at': '2018-02-09T20:48:22.086858'
    },
]


POST_LANDINGS_SUCCESS = {
  'id': 1
}

POST_LANDINGS_FAILURE_400 = {
    'detail': 'Bad Request Detail',
    'status': 400,
    'title': 'Bad Request',
    'type': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400'
}
