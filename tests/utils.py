# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def match_revision_and_diff_in_body(revision_id, diff_id):
    def matcher(request):
        try:
            params = request.json()
            return (
                params.get('revision_id') == revision_id and
                params.get('diff_id') == diff_id
            )
        except Exception:
            return False

    return matcher
