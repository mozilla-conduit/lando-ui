# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
A set of classes to facilitate Auth0 login using OIDC methodology
"""
import os

from flask_pyoidc.flask_pyoidc import OIDCAuthentication


class nullOpenIDConnect:
    """Null object for ensuring test cov if new up fails."""

    def __init__(self):
        """None based versions of OIDC object."""
        pass


class OIDCConfig:
    """Convienience object for returning required vars to flask."""

    def __init__(self):
        self.OIDC_DOMAIN = os.environ['OIDC_DOMAIN']
        self.OIDC_CLIENT_ID = os.environ['OIDC_CLIENT_ID']
        self.OIDC_CLIENT_SECRET = os.environ['OIDC_CLIENT_SECRET']
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


class OpenIDConnect:
    """Auth object for login, logout, and response validation."""

    def __init__(self, configuration):
        self.oidc_config = configuration

    def client_info(self):
        return dict(
            client_id=self.oidc_config.client_id(),
            client_secret=self.oidc_config.client_secret()
        )

    def provider_info(self):
        return dict(
            issuer=self.oidc_config.OIDC_DOMAIN,
            authorization_endpoint=self.oidc_config.auth_endpoint(),
            token_endpoint=self.oidc_config.token_endpoint(),
            userinfo_endpoint=self.oidc_config.userinfo_endpoint(),
        )

    def auth(self, app):
        oidc = OIDCAuthentication(
            app,
            provider_configuration_info=self.provider_info(),
            client_registration_info=self.client_info()
        )
        return oidc
