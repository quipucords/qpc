"""Test the CLI module's Insights Auth support."""

import http
from unittest.mock import patch

import pytest
from faker import Faker

from qpc.insights.auth import (
    DEVICE_AUTH_ENDPOINT_KEY,
    OPENID_CONFIG_ENDPOINT,
    TOKEN_ENDPOINT_KEY,
    InsightsAuth,
)
from qpc.insights.exceptions import InsightsAuthError
from qpc.utils import CONFIG_SSO_HOST_KEY, read_insights_config, write_insights_config

fake = Faker()


def get_sso_config_url():
    """Return the Insights SSO Configuration endpoint."""
    sso_host = read_insights_config().get(CONFIG_SSO_HOST_KEY)
    return f"https://{sso_host}{OPENID_CONFIG_ENDPOINT}"


class TestInsightsAuth:
    """Class for testing Insights Device Auth support."""

    @pytest.fixture
    def auth_token(self, faker):
        """Return a fake authentication token."""
        return faker.md5()

    @pytest.fixture
    def login_auth_response(self, faker):
        """Return a login authentication response."""
        user_code = faker.slug()
        verification_uri = faker.url()
        verification_uri_complete = f"{verification_uri}?user_code={user_code}"
        return {
            "device_code": faker.slug(),
            "user_code": user_code,
            "verification_uri": verification_uri,
            "verification_uri_complete": verification_uri_complete,
            "expires_in": 600,
            "interval": 5,
        }

    @pytest.fixture
    def stage_sso_host(self, faker):
        """Return an alternate staging sso host."""
        return f"stage-{faker.hostname()}"

    @pytest.mark.parametrize(
        "alt_sso_host",
        [None, f"stage-{fake.hostname()}"],
        ids=["default_sso_host", "stage_sso_host"],
    )
    def test_insights_request_auth(
        self, login_auth_response, faker, requests_mock, alt_sso_host
    ):
        """Testing that insights auth targets the right endpoint."""
        if alt_sso_host:
            write_insights_config({CONFIG_SSO_HOST_KEY: alt_sso_host})
        sso_url = faker.url()
        sso_config = {DEVICE_AUTH_ENDPOINT_KEY: sso_url}
        requests_mock.get(get_sso_config_url(), json=sso_config)
        requests_mock.post(sso_url, json=login_auth_response)
        assert InsightsAuth().request_auth() == login_auth_response

    def test_insights_request_auth_connection_error(self, stage_sso_host):
        """Testing that insights auth handles connection errors."""
        write_insights_config({CONFIG_SSO_HOST_KEY: stage_sso_host})
        with pytest.raises(InsightsAuthError) as err:
            InsightsAuth().request_auth()
        assert "Failed to request login authorization" in str(err.value)

    def test_insights_request_auth_invalid_sso_config(self, faker, requests_mock):
        """Testing that insights auth handles invalid SSO configuration errors."""
        with pytest.raises(InsightsAuthError) as err:
            sso_config = {faker.slug(): faker.hostname()}
            requests_mock.get(get_sso_config_url(), json=sso_config)
            InsightsAuth().request_auth()
        assert (
            "Failed to query the Insights SSO configuration:"
            f" missing {DEVICE_AUTH_ENDPOINT_KEY}" in str(err.value)
        )

    @pytest.mark.parametrize(
        "alt_sso_host",
        [None, f"stage-{fake.hostname()}"],
        ids=["default_sso_host", "stage_sso_host"],
    )
    def test_insights_wait_for_authorization_authorized(
        self, login_auth_response, auth_token, faker, requests_mock, alt_sso_host
    ):
        """Testing that insights wait for authorization returns the auth token."""
        if alt_sso_host:
            write_insights_config({CONFIG_SSO_HOST_KEY: alt_sso_host})
        insights_auth = InsightsAuth()
        insights_auth.auth_request = login_auth_response
        sso_token_url = faker.url()
        sso_config = {TOKEN_ENDPOINT_KEY: sso_token_url}
        requests_mock.get(get_sso_config_url(), json=sso_config)
        token_response = {"access_token": auth_token}
        requests_mock.post(sso_token_url, json=token_response)
        assert insights_auth.wait_for_authorization() == auth_token

    def test_insights_wait_for_authorization_connection_error(
        self, stage_sso_host, login_auth_response, auth_token
    ):
        """Testing that insights wait for authorization handles connection errors."""
        write_insights_config({CONFIG_SSO_HOST_KEY: stage_sso_host})
        insights_auth = InsightsAuth()
        insights_auth.auth_request = login_auth_response
        with pytest.raises(InsightsAuthError) as err:
            insights_auth.wait_for_authorization()
        assert "Failed to verify Login authorization" in str(err.value)

    def test_insights_wait_for_authorization_bad_request(
        self, login_auth_response, auth_token, faker, requests_mock
    ):
        """Testing that wait for authorization fails with failed checks."""
        insights_auth = InsightsAuth()
        insights_auth.auth_request = login_auth_response
        sso_token_url = faker.url()
        sso_config = {TOKEN_ENDPOINT_KEY: sso_token_url}
        requests_mock.get(get_sso_config_url(), json=sso_config)
        token_response = {"error": "unknown_error"}
        requests_mock.post(
            sso_token_url, status_code=http.HTTPStatus.BAD_REQUEST, json=token_response
        )
        with pytest.raises(InsightsAuthError) as err:
            insights_auth.wait_for_authorization()
        assert "Failed to verify Login authorization" in str(err.value)

    @patch("time.sleep")
    def test_insights_wait_for_authorization_expired(
        self, mock_sleep, faker, requests_mock
    ):
        """Testing that authorization pending checks for expired time."""
        insights_auth = InsightsAuth()
        insights_auth.auth_request = {
            "device_code": faker.slug(),
            "user_code": faker.slug(),
            "verification_uri": faker.url(),
            "verification_uri_complete": faker.url(),
            "expires_in": 0,
            "interval": 1,
        }
        mock_sleep.return_value = None
        sso_token_url = faker.url()
        sso_config = {TOKEN_ENDPOINT_KEY: sso_token_url}
        requests_mock.get(get_sso_config_url(), json=sso_config)
        token_response = {
            "error": "authorization_pending",
            "error_description": "The authorization request is still pending",
        }
        requests_mock.post(
            sso_token_url, status_code=http.HTTPStatus.BAD_REQUEST, json=token_response
        )
        with pytest.raises(InsightsAuthError) as err:
            insights_auth.wait_for_authorization()
        assert "Time-out while waiting for Login authorization" in str(err.value)

    def test_insights_wait_for_authorization_expired_from_sso(
        self, login_auth_response, faker, requests_mock
    ):
        """Testing that token authorization expired from the sso server."""
        insights_auth = InsightsAuth()
        insights_auth.auth_request = login_auth_response
        sso_token_url = faker.url()
        sso_config = {TOKEN_ENDPOINT_KEY: sso_token_url}
        requests_mock.get(get_sso_config_url(), json=sso_config)
        token_response = {
            "error": "expired_token",
            "error_description": "Device code is expired",
        }
        requests_mock.post(
            sso_token_url, status_code=http.HTTPStatus.BAD_REQUEST, json=token_response
        )
        with pytest.raises(InsightsAuthError) as err:
            insights_auth.wait_for_authorization()
        assert "Time-out while waiting for Login authorization" in str(err.value)
