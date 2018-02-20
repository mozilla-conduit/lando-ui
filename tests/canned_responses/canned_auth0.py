# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# yapf: disable
# flake8: noqa

VALID_ID_TOKEN = {
    "aud": ["aud_string"],
    "email": "testuser@mozilla.example",
    "email_verified": True,
    "exp": 1519767792,
    "family_name": "User",
    "given_name": "Test",
    "iat": 1519162992,
    "iss": "https://auth.mozilla.auth0.com/",
    "name": "Test User",
    "nickname": "Test User",
    "nonce": "nouce_string",
    "picture": "https://pictures.example/face.png",
    "sub": "ad|Mozilla-LDAP|testuser",
    "updated_at": "2018-02-20T21:43:12.202Z"
}

VALID_ACCESS_TOKEN = "valid_access_token_string"

VALID_USERINFO = {
    "email": "testuser@mozilla.example",
    "email_verified": True,
    "family_name": "User",
    "given_name": "Test",
    "name": "Test User",
    "nickname": "Test User",
    "picture": "https://pictures.example/face.png",
    "sub": "ad|Mozilla-LDAP|testuser",
    "updated_at": "2018-02-20T21:43:12.202Z"
}
