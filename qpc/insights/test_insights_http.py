"""Tests for the HTTP Client for console.redhat.com."""
from unittest import mock

import pytest

from qpc.insights.http import InsightsClient


@mock.patch("requests.Session.request")
@pytest.mark.parametrize(
    "base_url, method, url, full_url",
    [
        (
            "https://testconsole.redhat.com",
            "post",
            "/v1/path/to/resource",
            "https://testconsole.redhat.com/v1/path/to/resource",
        ),
        (
            "",
            "put",
            "https://testconsole.redhat.com/v1/path/to/resource",
            "https://testconsole.redhat.com/v1/path/to/resource",
        ),
        (
            None,
            "get",
            "https://testconsole.redhat.com/v1/path/to/resource",
            "https://testconsole.redhat.com/v1/path/to/resource",
        ),
    ],
)
def test_request_joins_url_with_base_url(
    request_session_mocker, base_url, method, url, full_url
):
    """Test if urljoin is performed successfully."""
    insights_client_session = InsightsClient(base_url=base_url)

    insights_client_session.request(method, url)

    request_session_mocker.assert_called_with(method, full_url)


@mock.patch("requests.Session.request")
@pytest.mark.parametrize(
    "base_url, url, args, full_url",
    [
        (
            "https://testconsole.redhat.com",
            "/v1/path/to/resource",
            {"file": "file"},
            "https://testconsole.redhat.com/v1/path/to/resource",
        ),
        (
            "",
            "https://testconsole.redhat.com/v1/path/to/resource",
            {"data": {"key": "value"}, "file": "file"},
            "https://testconsole.redhat.com/v1/path/to/resource",
        ),
        (
            None,
            "https://testconsole.redhat.com/v1/path/to/resource",
            {"proxies": "proxy-test-value"},
            "https://testconsole.redhat.com/v1/path/to/resource",
        ),
    ],
)
def test_extra_args_are_passed_to_request(
    request_session_mocker,
    base_url,
    url,
    args,
    full_url,
):
    """Test if parent class receives all args passed."""
    insights_client_session = InsightsClient(base_url=base_url)

    insights_client_session.request("post", url, args)

    request_session_mocker.assert_called_with("post", full_url, args)


def test_auth():
    """Test if auth is being passed with the right parameters."""
    client = InsightsClient(auth=("test-username", "test-password"))
    assert client.auth == ("test-username", "test-password")
