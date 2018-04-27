# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def match_landing_request(revision_id, diff_id, confirmation_token=None):
    def matcher(request):
        try:
            params = request.json()
            return (
                params.get('revision_id') == revision_id and
                params.get('diff_id') == diff_id and
                params.get('confirmation_token') == confirmation_token
            )
        except Exception:
            return False

    return matcher
