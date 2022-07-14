# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
"""Tests for the HTTP Client for console.redhat.com."""
from unittest import mock

import pytest

from qpc.insights.http import InsightsClient


@mock.patch("requests.Session.request")
@pytest.mark.parametrize(
    "base_url, method, url, result",
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
    request_session_mocker, base_url, method, url, result
):
    """Test if urljoin is performed successfully."""
    insights_client_session = InsightsClient(
        base_url=base_url, auth=("username", "pass")
    )

    insights_client_session.request(method, url)

    request_session_mocker.assert_called_with(method, result)


@mock.patch("requests.Session.request")
@pytest.mark.parametrize(
    "base_url, url, args, result",
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
    result,
):
    """Test if parent class receives all args passed."""
    insights_client_session = InsightsClient(
        base_url=base_url, auth=("username", "pass")
    )

    insights_client_session.request("post", url, args)

    request_session_mocker.assert_called_with("post", result, args)
