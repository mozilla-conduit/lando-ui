# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
A set of classes to facilitate Auth0 login using OIDC methodology
"""
import os

from flask_pyoidc.flask_pyoidc import OIDCAuthentication


class OIDCConfig:
    """Convenience object for returning required vars to flask."""

    def __init__(self):
        self.OIDC_DOMAIN = os.environ['OIDC_DOMAIN']
        self.OIDC_CLIENT_ID = os.environ['OIDC_CLIENT_ID']
        self.OIDC_CLIENT_SECRET = os.environ['OIDC_CLIENT_SECRET']
        self.LANDO_API_OIDC_IDENTIFIER = (
            os.environ['LANDO_API_OIDC_IDENTIFIER']
        )
        self.LOGIN_URL = 'https://{DOMAIN}/login?client={CLIENT_ID}'.format(
            DOMAIN=self.OIDC_DOMAIN, CLIENT_ID=self.OIDC_CLIENT_ID
        )

    def auth_endpoint(self):
        return 'https://{DOMAIN}/authorize'.format(DOMAIN=self.OIDC_DOMAIN)

    def token_endpoint(self):
        return 'https://{DOMAIN}/oauth/token'.format(DOMAIN=self.OIDC_DOMAIN)

    def userinfo_endpoint(self):
        return 'https://{DOMAIN}/userinfo'.format(DOMAIN=self.OIDC_DOMAIN)

    def client_id(self):
        return self.OIDC_CLIENT_ID

    def client_secret(self):
        return self.OIDC_CLIENT_SECRET

    def lando_api_oidc_id(self):
        return self.LANDO_API_OIDC_IDENTIFIER


class OpenIDConnect:
    """Auth object for login, logout, and response validation."""

    def __init__(self, configuration):
        self.oidc_config = configuration

    def client_info(self):
        return dict(
            client_id=self.oidc_config.client_id(),
            client_secret=self.oidc_config.client_secret(),
            session_refresh_interval_seconds=900  # 15 minutes
        )

    def provider_info(self):
        return dict(
            issuer=self.oidc_config.OIDC_DOMAIN,
            authorization_endpoint=self.oidc_config.auth_endpoint(),
            token_endpoint=self.oidc_config.token_endpoint(),
            userinfo_endpoint=self.oidc_config.userinfo_endpoint(),
        )

    def auth(self, app):
        """ Creates the OIDCAuthentication object to be used to protect routes.

        Authentication is requested with the following audiences:
        - lando-api: The LANDO_API_OIDC_IDENTIFIER environment variable will
            be included as an audience. This allows lando-api to verify that
            tokens created by lando-ui were intended to be used by the api.

        Authentication is requested with the following scopes:
        - openid - Permission to get a unique identifier for the user. This
            also permits querying Auth0 at https://OIDC_DOMAIN/userinfo for
            additional user information.
        - email - Permission to get the user's email address.
        - profile - Permission to get additional information about the user
          such as their real name, picture url, and LDAP information.
        """
        oidc = OIDCAuthentication(
            app,
            provider_configuration_info=self.provider_info(),
            client_registration_info=self.client_info(),
            extra_request_args={
                "audience": [self.oidc_config.lando_api_oidc_id()],
                'scope': ['openid', 'profile', 'email', 'lando']
            }
        )
        return oidc
