# Copyright 2020 Mozilla Foundation
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
# https://github.com/zamzterz/Flask-pyoidc/blob/v3.2.0/src/flask_pyoidc/pyoidc_facade.py

"""
This module implements two wrappers, `parse_response_wrapper` and `userinfo_request_wrapper`. Both
methods return methods that are used to override functionality in
`flask_pyoidc.pyoidc_facade.PyoidcFacade` in order to properly parse the returned response from
Auth0.
"""


from landoui.support.pyoidc import IdToken, AccessTokenResponse


def parse_response_wrapper(auth0):
    def _parse_response(
            response_params, success_response_cls, error_response_cls):
        """Parse response from the client and return a token response object.

        This method is modified from the original version to support a custom
        AccessTokenResponse class. If the response contains an ID token, we
        use the custom class, otherwise, use whatever class is provided.

        Args:
            response_params (dict)
            success_response_cls:
              Used if we do not have an error response and if the respose
              does not contain an id_token.
            error_response_cls: used if there is an error in the response

        Returns:
            `oic.oic.message.AuthorizationResponse` or
            `landoui.support.pyoidc.AccessTokenResponse` if there is no error,
            otherwise returns `oic.oic.message.TokenErrorResponse`.
        """
        if 'error' in response_params:
            response = error_response_cls(**response_params)
        else:
            if "id_token" in response_params:
                response = AccessTokenResponse(**response_params)
            else:
                response = success_response_cls(**response_params)
            response.verify(keyjar=auth0._client.keyjar)
        return response
    return _parse_response


def userinfo_request_wrapper(auth0):
    def userinfo_request(access_token):
        """Fetch user info from the auth client.

        This method is modified from the original version to support the custom
        IdToken schema.

        Args:
            access_token (str): base64 encoded string

        Returns:
            landoui.support.pyoidc.IdToken
        """
        http_method = (
            auth0._provider_configuration.userinfo_endpoint_method)
        if not access_token or http_method is None or (
                not auth0._client.userinfo_endpoint):
            return None
        userinfo_response = auth0._client.do_user_info_request(
                method=http_method,
                token=access_token,
                user_info_schema=IdToken)
        return userinfo_response
    return userinfo_request
