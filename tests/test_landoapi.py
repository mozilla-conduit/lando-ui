# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest
import requests
import requests_mock

from landoui.landoapi import (
    LandoAPI,
    LandoAPIError,
    LandoAPICommunicationException,
)


@pytest.mark.parametrize(
    'exc', [
        requests.ConnectionError,
        requests.Timeout,
        requests.ConnectTimeout,
        requests.TooManyRedirects,
    ]
)
def test_raise_communication_exception_on_request_exceptions(api_url, exc):
    api = LandoAPI(api_url)
    with requests_mock.mock() as m:
        m.get(api_url + '/stacks/D1', exc=exc)

        with pytest.raises(LandoAPICommunicationException):
            api.request('GET', 'stacks/D1')

        assert m.called


def test_raise_communication_exception_on_invalid_json(api_url):
    api = LandoAPI(api_url)
    with requests_mock.mock() as m:
        m.get(api_url + '/stacks/D1', text='invalid } json {[[')

        with pytest.raises(LandoAPICommunicationException):
            api.request('GET', 'stacks/D1')

        assert m.called


@pytest.mark.parametrize(
    'status, body', [
        (404, '[]'),
        (500, '{}'),
        (500, '{"detail": "detail", "instance": "instance"}'),
        (400, '{}'),
        (401, '{}'),
    ]
)
def test_raise_error_exception_on_error_response(api_url, status, body):
    api = LandoAPI(api_url)
    with requests_mock.mock() as m:
        m.get(api_url + '/stacks/D1', status_code=status, text=body)

        with pytest.raises(LandoAPIError):
            api.request('GET', 'stacks/D1')

        assert m.called


def test_raise_error_with_details_on_error_response(api_url):
    api = LandoAPI(api_url)
    error = {
        'detail': 'Couldn\'t find it',
        'status': 404,
        'title': 'Not Found',
        'type': 'about:blank',
    }
    with requests_mock.mock() as m:
        m.get(api_url + '/stacks/D1', status_code=error['status'], json=error)

        with pytest.raises(LandoAPIError) as exc_info:
            api.request('GET', 'stacks/D1')

        assert m.called
        assert exc_info.value.detail == error['detail']
        assert exc_info.value.title == error['title']
        assert exc_info.value.type == error['type']
        assert exc_info.value.status_code == error['status']
        assert exc_info.value.response == error
        assert exc_info.value.instance is None
