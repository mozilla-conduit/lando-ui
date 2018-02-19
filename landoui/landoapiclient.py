import json
import logging
import requests

from landoui.errorhandlers import UIError, RevisionNotFound
from landoui.sentry import sentry

logger = logging.getLogger(__name__)


class LandoAPIClient:
    """A class to interface with Lando API.

    Attributes:
        landoapi_url: The URL of the Lando API instance to access.

        phabricator_api_token: The Phabricator API Token to be sent along with
            each request to Lando API. If a token is provided it will be used
            by the api to allow it to access private data that the owner of the
            api token has access to. If not provided, only public data from
            Phabricator will be accessible.

        auth0_access_token: The Auth0 Access Token to but sent along with each
            request to Lando API that requires it, namely to land changes. This
            access token will be used to identify and authorize the user before
            performing the requested action.
    """

    def __init__(
        self,
        landoapi_url,
        phabricator_api_token=None,
        auth0_access_token=None
    ):
        self.landoapi_url = landoapi_url
        self.phabricator_api_token = phabricator_api_token
        self.auth0_access_token = auth0_access_token

    def get_revision(self, revision_id, diff_id=None):
        """Queries Lando API's GET /revisions/{id} endpoint.

        Args:
            revision_id: The revision id to lookup in 'D123' format.
            diff_id: A specific diff id belonging to the revision whose info
                 will be included in the response. If None, then the most
                 recent diff of the revision will be included.

        Returns:
            If successful, a dictionary containing the revision information.
            Does not return if unsuccessful.

        Exceptions:
            If the revision/diff combination is not found or the user does not
            have permission to view it, then an errorhandlers.RevisionNotFound
            exception will be raised. If this is not caught, a default handler
            will show a 404 page.

            If there are any other exceptions with communicating with lando-api
            and creating the response then an errorhandlers.UIError will be
            raised. If this is not caught, a default handler will show an error
            message page.
        """
        get_revision_url = '{host}/revisions/{revision_id}'.format(
            host=self.landoapi_url, revision_id=revision_id
        )

        try:
            # TODO: Use the phabricator_api_token if provided to allow
            # the user to view private revisions.
            response = requests.get(
                get_revision_url, params={'diff_id': diff_id}
            )

            if response.status_code == 404:
                raise RevisionNotFound(revision_id, diff_id)
            else:
                response.raise_for_status()
                return response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            logger.error(
                {
                    'url': get_revision_url,
                    'revision_id': revision_id,
                    'diff_id': diff_id,
                    'exception_type': str(type(e)),
                    'exception_message': str(e)
                }, 'get_revision.exception'
            )

            error_details = {
                'title': 'Failed to reach Lando API',
                'message': (
                    'Lando API is unable to process the request right now. '
                    'Try again later.'
                ),
            }  # yapf: disable
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                error_details['status_code'] = e.response.status_code
            raise UIError(**error_details)

    def get_landings(self, revision_id):
        """Queries Lando API's GET /landings endpoint.

        Args:
            revision_id: The revision id, in 'D123' format, to filter landings
                by.

        Returns:
            An array of dictionaries for each landing. Or, an empty array if
            no landings are found. Does not return if unsuccessful in making
            the request and getting a valid response.

        Exceptions:
            If the revision does not exist or the user does not have permission
            to view it, then an errorhandlers.RevisionNotFound exception will
            be raised. If this is not caught, a default handler will show a 404
            page.

            If there are any other exceptions with communicating with lando-api
            and creating the response then the landoui.errorhandlers.UIError
            will be raised. If this is not caught, a default handler will show
            a default error message page.
        """
        get_landings_url = '{host}/landings'.format(host=self.landoapi_url)

        try:
            # TODO: Use the phabricator_api_token if provided to allow
            # the user to view landings of private revisions
            response = requests.get(
                get_landings_url, params={'revision_id': revision_id}
            )

            if response.status_code == 404:
                raise RevisionNotFound(revision_id)
            else:
                response.raise_for_status()
                return response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            logger.error(
                {
                    'url': get_landings_url,
                    'revision_id': revision_id,
                    'exception_type': str(type(e)),
                    'exception_message': str(e)
                }, 'get_landings.exception'
            )

            error_details = {
                'title': 'Failed to reach Lando API',
                'message': (
                    'Lando API is unable to process the request right now. '
                    'Try again later.'
                ),
            }  # yapf: disable
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                error_details['status_code'] = e.response.status_code
            raise UIError(**error_details)

    def post_landings(self, revision_id, diff_id):
        """Submit a land request to lando-api via the POST /landings endpoint.

        Args:
            revision_id: The id of the revision to land in 'D123' format.
            diff_id: The id of the specific diff of the revision to land.

        Returns:
            If successful, returns True. Does not return if unsuccessful.

        Exceptions:
            If the landing submission fails for any reason, a
            LandingSubmissionError will be raised.
        """
        # Double check the user is logged in to provide a helpful message.
        if not self.auth0_access_token:
            raise LandingSubmissionError('You must be logged in to land.')

        # Setup request
        post_landings_url = '{host}/landings'.format(host=self.landoapi_url)
        params = {
            'revision_id': revision_id,
            'diff_id': int(diff_id),
        }
        headers = {
            'Authorization': 'Bearer {}'.format(self.auth0_access_token),
            'Content-Type': 'application/json',
        }

        # Make request and handle response
        try:
            land_response = requests.post(
                post_landings_url, json=params, headers=headers
            )
            land_response.raise_for_status()
            if land_response.status_code not in (200, 202):
                logger.error(
                    {
                        'url': post_landings_url,
                        'revision_id': revision_id,
                        'diff_id': diff_id,
                        'status_code': land_response.status_code,
                        'response_body': land_response.text
                    }, 'post_landings.invalid_2xx_code'
                )
                sentry.captureMessage('landoapi returned an unexpected 2xx')

                raise LandingSubmissionError(
                    'Lando API did not respond successfully. '
                    'Please try again later.'
                )
            return True
        except requests.HTTPError as e:
            # All HTTP errors from Lando API should be in the Connexions
            # problem exception format and include title, detail, and type.
            try:
                problem = e.response.json()
                problem_message = (
                    '{title}: {detail}'.format(
                        title=problem['title'], detail=problem['detail']
                    )
                )
            except (json.JSONDecodeError, KeyError) as e2:
                logger.error(
                    {
                        'url': post_landings_url,
                        'revision_id': revision_id,
                        'diff_id': diff_id,
                        'status_code': e.response.status_code,
                        'response_body': e.response.text,
                        'exception_type': str(type(e2)),
                        'exception_message': str(e2)
                    }, 'post_landings.failed_reading_http_error'
                )
                sentry.captureException()

                raise LandingSubmissionError(
                    'Lando API did not respond successfully. '
                    'Please try again later.'
                )

            logger.debug(
                {
                    'url': post_landings_url,
                    'revision_id': revision_id,
                    'diff_id': diff_id,
                    'status_code': e.response.status_code,
                    'problem_message': problem_message,
                    'problem_type': problem.get('type')
                }, 'post_landings.failed_landing'
            )
            raise LandingSubmissionError(
                error=problem_message, link=problem.get('type')
            )
        except requests.RequestException:
            logger.debug(
                {
                    'url': post_landings_url,
                    'revision_id': revision_id,
                    'diff_id': diff_id,
                }, 'post_landings.failed_connection_to_landoapi'
            )
            raise LandingSubmissionError(
                'Failed to connect to Lando API. '
                'Please try again later.'
            )

    def post_landings_dryrun(self, revision_id, diff_id):
        """Queries Lando API's /landings/dryrun endpoint.

        The dryrun checks if there are any issues before landings.
        Issues can one be either a warning or a blocker.
        Users may acknowledge a warning and continue landing.
        If there are any blockers, landing is blocked until those resolve.

        Lando API also provides a confirmation token which is expected when
        performing the real landing via the POST /landings endpoint. This token
        tells the API that we've properly tried a dryrun first and acknowledged
        any warnings.

        Returns a dictionary with the following format:
        {
            'confirmation_token': token,
            'warnings': [{'id': id, 'message': message}, ...],
            'blockers': [{'id': id, 'message': message}, ...]
        }

        TODO: Exception Handling
        """
        # TODO Replace me with a query to the real dryrun endpoint.
        # Tracked in: https://trello.com/c/dh0c0YTs/
        result = {
            'confirmation_token': 'placeholder',
            'warnings': [],
            'blockers': []
        }
        return result


class LandingSubmissionError(Exception):
    """Custom Exception to hold information when a landing immediately fails.

    Attributes:
        error: Human readable message with details of what happened.
        link: An optional link to a resource that further describes the error.
    """

    def __init__(self, error, link=None):
        full_message = '{} ({})'.format(error, link) if link else error
        super().__init__(full_message)
        self.error = error
        self.link = link
