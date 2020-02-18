# Copyright 2020 Mozilla Foundation
# Copyright (C) 2017 Roland Hedberg, Sweden
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# The code in this module is modified from its original version. The original
# version can be found at
# https://github.com/OpenIDC/pyoidc/blob/v1.1.2/src/oic/oic/message.py

"""
This module implements a custom `IdToken` class that inherits from
`oic.oic.message.IdToken`, as well as an `AccessTokenResponse` class that is used to
override the verification of the ID token.
"""


from datetime import datetime

from oic.oauth2 import message as oauth2_message
from oic.oic import message as oic_message


class IdToken(oic_message.IdToken):
    """Custom OpenID schema to work around a bug in Auth0's response

    Auth0's identity token contains a string value for the "updated_at" key.
    flask_pyoidc and oic expect a timestamp (int) value, so this works around
    the problem by specifying a custom type and serializer/deserializer.

    This is a known issue with Auth0, which they have a fix for but is not
    enabled for Mozilla.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.c_param["updated_at"] = oauth2_message.ParamDefinition(
            datetime,
            False,
            lambda d, *args: f"{datetime.fromtimestamp(d).isoformat()}Z",
            lambda d, **kwargs: int(datetime.fromisoformat(d[:-1]).timestamp()),
            True,
        )


class AccessTokenResponse(oauth2_message.AccessTokenResponse):
    """Custom Message subclass to work around a bug with Auth0

    We create this class so that we can use our own verify_id_token method.
    """

    @staticmethod
    def verify_id_token(instance, keyjar):
        """Extract and verify an ID token.

        This method is modified from the original version to override IdToken
        with our own.

        Args:
            instance (landoui.support.pyoidc.AccessTokenResponse)
            keyjar (KeyJar)

        Returns:
            `landoui.support.pyoidc.IdToken`
        """
        # Try to decode the JWT, checks the signature
        _jws = str(instance["id_token"])

        # It can be encrypted, so try to decrypt first
        _packer = oic_message.JWT()
        _body = _packer.unpack(_jws).payload()

        try:
            if _body["iss"] not in keyjar:
                raise ValueError("Unknown issuer")
        except KeyError:
            raise oic_message.MissingRequiredAttribute("iss")

        idt = IdToken().from_jwt(_jws, keyjar=keyjar)
        if not idt.verify(keyjar=keyjar):
            raise oic_message.VerificationError("Could not verify id_token", idt)

        return idt

    c_param = oauth2_message.AccessTokenResponse.c_param.copy()
    c_param.update({"id_token": oauth2_message.SINGLE_OPTIONAL_STRING})

    def verify(self, **kwargs):
        super().verify(**kwargs)
        if "id_token" in self:
            # replace the JWT with the verified IdToken instance
            self["id_token"] = self.verify_id_token(self, **kwargs)
        return True
