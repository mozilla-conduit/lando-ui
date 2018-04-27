# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest
import requests
import requests_mock

from landoui.errorhandlers import UIError, RevisionNotFound
from landoui.landoapiclient import LandoAPIClient, LandingSubmissionError

from tests.canned_responses import canned_landoapi
from tests.utils import match_landing_request


def test_get_revision_success(api_url):
    landoapi = LandoAPIClient(api_url)
    with requests_mock.mock() as m:
        m.get(
            api_url + '/revisions/D1',
            json=canned_landoapi.GET_REVISION_DEFAULT
        )
        revision = landoapi.get_revision('D1')
    assert revision == canned_landoapi.GET_REVISION_DEFAULT


def test_get_revision_404(api_url):
    landoapi = LandoAPIClient(api_url)
    with requests_mock.mock() as m:
        m.get(
            api_url + '/revisions/D1',
            status_code=404,
            json=canned_landoapi.PROBLEM_REVISION_NOT_FOUND
        )

        with pytest.raises(RevisionNotFound) as exc_info:
            landoapi.get_revision('D1', 100)

        assert 'D1' in str(exc_info.value)
        assert 'Diff 100' in str(exc_info.value)


def test_get_revision_500_failure(api_url):
    landoapi = LandoAPIClient(api_url)
    with requests_mock.mock() as m:
        m.get(
            api_url + '/revisions/D1',
            status_code=500,
        )
        with pytest.raises(UIError) as exc_info:
            landoapi.get_revision('D1')

        assert 'Failed to reach Lando API' == exc_info.value.title


def test_get_revision_connection_failure(api_url):
    landoapi = LandoAPIClient(api_url)
    with requests_mock.mock() as m:
        m.get(
            api_url + '/revisions/D1', exc=requests.exceptions.ConnectTimeout
        )
        with pytest.raises(UIError) as exc_info:
            landoapi.get_revision('D1')

        assert 'Failed to reach Lando API' == exc_info.value.title


def test_get_landings_success(api_url):
    landoapi = LandoAPIClient(api_url)
    with requests_mock.mock() as m:
        m.get(
            api_url + '/landings?revision_id=D1',
            json=canned_landoapi.GET_LANDINGS_DEFAULT
        )
        landings = landoapi.get_landings('D1')
    assert landings == canned_landoapi.GET_LANDINGS_DEFAULT


def test_get_landings_500_failure(api_url):
    landoapi = LandoAPIClient(api_url)
    with requests_mock.mock() as m:
        m.get(
            api_url + '/landings?revision_id=D1',
            status_code=500,
        )
        with pytest.raises(UIError) as exc_info:
            landoapi.get_landings('D1')

        assert 'Failed to reach Lando API' == exc_info.value.title


def test_get_landings_connection_failure(api_url):
    landoapi = LandoAPIClient(api_url)
    with requests_mock.mock() as m:
        m.get(
            api_url + '/landings?revision_id=D1',
            exc=requests.exceptions.ConnectTimeout
        )
        with pytest.raises(UIError) as exc_info:
            landoapi.get_landings('D1')

        assert 'Failed to reach Lando API' == exc_info.value.title


def test_post_landings_success(api_url):
    landoapi = LandoAPIClient(api_url, auth0_access_token='access_token')
    with requests_mock.mock() as m:
        m.post(
            api_url + '/landings',
            additional_matcher=match_landing_request('D1', 1, 'confirmed'),
            json=canned_landoapi.POST_LANDINGS_SUCCESS
        )
        assert landoapi.post_landings('D1', 1, 'confirmed')


def test_post_landings_no_access_token(api_url):
    landoapi = LandoAPIClient(api_url, auth0_access_token=None)
    with requests_mock.mock() as m:
        m.post(
            api_url + '/landings',
            additional_matcher=match_landing_request('D1', 1),
            json=canned_landoapi.POST_LANDINGS_SUCCESS
        )
        with pytest.raises(AssertionError):
            landoapi.post_landings('D1', 1, None)


def test_post_landings_unexpected_2xx_code(api_url):
    landoapi = LandoAPIClient(api_url, auth0_access_token='access_token')
    with requests_mock.mock() as m:
        m.post(
            api_url + '/landings',
            additional_matcher=match_landing_request('D1', 1),
            json={},
            status_code=204
        )
        with pytest.raises(LandingSubmissionError) as exc_info:
            landoapi.post_landings('D1', 1, None)

    assert 'Lando API did not respond successfully.' in exc_info.value.error


def test_post_landings_http_error_with_valid_response(api_url):
    landoapi = LandoAPIClient(api_url, auth0_access_token='access_token')
    with requests_mock.mock() as m:
        m.post(
            api_url + '/landings',
            additional_matcher=match_landing_request('D1', 1),
            json=canned_landoapi.PROBLEM_BAD_REQUEST,
            status_code=400
        )
        with pytest.raises(LandingSubmissionError) as exc_info:
            landoapi.post_landings('D1', 1, None)

    assert 'Bad Request: Bad Request Detail' in exc_info.value.error


def test_post_landings_http_error_without_valid_response(api_url):
    landoapi = LandoAPIClient(api_url, auth0_access_token='access_token')
    with requests_mock.mock() as m:
        m.post(
            api_url + '/landings',
            additional_matcher=match_landing_request('D1', 1),
            status_code=400
        )
        with pytest.raises(LandingSubmissionError) as exc_info:
            landoapi.post_landings('D1', 1, None)

    assert 'Lando API did not respond successfully.' in exc_info.value.error


def test_post_landings_connection_error(api_url):
    landoapi = LandoAPIClient(api_url, auth0_access_token='access_token')
    with requests_mock.mock() as m:
        m.post(
            api_url + '/landings',
            additional_matcher=match_landing_request('D1', 1),
            exc=requests.exceptions.ConnectTimeout
        )
        with pytest.raises(LandingSubmissionError) as exc_info:
            landoapi.post_landings('D1', 1, None)

    assert 'Failed to connect to Lando API.' in exc_info.value.error


def test_post_landings_dryrun_success(api_url):
    landoapi = LandoAPIClient(api_url, auth0_access_token='access_token')
    with requests_mock.mock() as m:
        m.post(
            api_url + '/landings/dryrun',
            additional_matcher=match_landing_request('D1', 1),
            json=canned_landoapi.POST_LANDINGS_DRYRUN_SUCCESS
        )
        result = landoapi.post_landings_dryrun('D1', 1)

    assert canned_landoapi.POST_LANDINGS_DRYRUN_SUCCESS == result


def test_post_landings_dryrun_no_access_token(api_url):
    landoapi = LandoAPIClient(api_url, auth0_access_token=None)
    with requests_mock.mock() as m:
        m.post(
            api_url + '/landings/dryrun',
            additional_matcher=match_landing_request('D1', 1),
            json=canned_landoapi.POST_LANDINGS_DRYRUN_SUCCESS
        )
        with pytest.raises(AssertionError):
            landoapi.post_landings_dryrun('D1', 1)


def test_post_landings_dryrun_http_error_with_valid_response(api_url):
    landoapi = LandoAPIClient(api_url, auth0_access_token='access_token')
    with requests_mock.mock() as m:
        m.post(
            api_url + '/landings/dryrun',
            additional_matcher=match_landing_request('D1', 1),
            json=canned_landoapi.PROBLEM_BAD_REQUEST,
            status_code=400
        )
        with pytest.raises(UIError) as exc_info:
            landoapi.post_landings_dryrun('D1', 1)

    assert 'Bad Request' in exc_info.value.title
    assert 'Bad Request Detail' in exc_info.value.message
    assert 400 == exc_info.value.status_code


def test_post_landings_dryrun_http_error_without_valid_response(api_url):
    landoapi = LandoAPIClient(api_url, auth0_access_token='access_token')
    with requests_mock.mock() as m:
        m.post(
            api_url + '/landings/dryrun',
            additional_matcher=match_landing_request('D1', 1),
            status_code=400
        )
        with pytest.raises(UIError) as exc_info:
            landoapi.post_landings_dryrun('D1', 1)

    assert 'Lando API did not respond successfully.' == exc_info.value.title
    assert 400 == exc_info.value.status_code


def test_post_landings_dryrun_connection_error(api_url):
    landoapi = LandoAPIClient(api_url, auth0_access_token='access_token')
    with requests_mock.mock() as m:
        m.post(
            api_url + '/landings/dryrun',
            additional_matcher=match_landing_request('D1', 1),
            exc=requests.exceptions.ConnectTimeout
        )
        with pytest.raises(UIError) as exc_info:
            landoapi.post_landings_dryrun('D1', 1)

    assert 'Failed to connect to Lando API.' in exc_info.value.title
