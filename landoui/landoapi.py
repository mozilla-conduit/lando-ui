# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import requests
from json.decoder import JSONDecodeError

logger = logging.getLogger(__name__)


class LandoAPI:
    """Client for Lando API."""

    def __init__(
        self, url, *, phabricator_api_token=None, auth0_access_token=None, session=None
    ):
        self.url = url + "/" if url[-1] == "/" else url + "/"
        self.phabricator_api_token = phabricator_api_token
        self.auth0_access_token = auth0_access_token
        self.session = session or self.create_session()

    @staticmethod
    def create_session():
        return requests.Session()

    def request(self, method, url_path, *, require_auth0=False, **kwargs):
        """Return the response of a request to Lando API.

        Args:
            method: HTTP method to use for request.
            url_path: Path to be appended to api url for request.
            require_auth0: Should an auth0 token be required and sent.
            **kwargs: All other kwargs passed to underlying requests.

        Returns:
            JSON decoded response from Lando API

        Raises:
            LandoAPIException:
                Base exception class for other exceptions.
            LandoAPIError:
                If the API returns an error response.
            LandoAPICommunicationException:
                If there is an error communicating with the API.
        """
        headers = {
            "Content-Type": "application/json",
        }

        if require_auth0:
            assert self.auth0_access_token is not None
            headers["Authorization"] = "Bearer {}".format(self.auth0_access_token)

        if self.phabricator_api_token:
            headers["X-Phabricator-API-Key"] = self.phabricator_api_token

        headers.update(kwargs.get("headers", {}))
        kwargs["headers"] = headers

        try:
            response = self.session.request(method, self.url + url_path, **kwargs)

            logger.debug(
                "lando-api response",
                extra={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                },
            )

        except requests.RequestException as exc:
            raise LandoAPICommunicationException(
                "An error occurred when communicating with Lando API"
            ) from exc

        try:
            data = response.json()
        except JSONDecodeError as exc:
            response.raise_for_status()

            raise LandoAPICommunicationException(
                "Lando API response could not be decoded as JSON"
            ) from exc

        LandoAPIError.raise_if_error(response, data)
        return data


class LandoAPIException(Exception):
    """Exception from LandoAPI."""


class LandoAPICommunicationException(LandoAPIException):
    """Exception when communicating with Lando API fails."""


class LandoAPIError(LandoAPIException):
    """Exception when Lando API responds with an error."""

    def __init__(self, status_code, data):
        self.status_code = status_code

        # Error responses should have the RFC 7807 fields at minimum
        # but could include other data, so tack on the response.
        self.response = data

        self.detail = None
        self.instance = None
        self.status = None
        self.title = None
        self.type = None

        try:
            self.detail = data.get("detail")
            self.instance = data.get("instance")
            self.status = data.get("status")
            self.title = data.get("title")
            self.type = data.get("type")
        except AttributeError:
            # Data wasn't a dictionary.
            pass

        super().__init__(self.detail or "")

    @classmethod
    def raise_if_error(cls, response_obj, data):
        if response_obj.status_code < 400:
            return

        raise cls(response_obj.status_code, data)
