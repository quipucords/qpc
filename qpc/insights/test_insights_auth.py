"""Test the CLI module's Insights Auth support."""

import http
from unittest.mock import patch

import pytest

from qpc.insights.auth import DEVICE_AUTH_ENDPOINT, TOKEN_ENDPOINT, InsightsAuth
from qpc.insights.exceptions import InsightsAuthError
from qpc.utils import CONFIG_SSO_HOST_KEY, read_insights_config, write_insights_config


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

    def test_insights_request_auth(self, login_auth_response, faker, requests_mock):
        """Testing that insights auth targets the right endpoint."""
        sso_host = read_insights_config().get(CONFIG_SSO_HOST_KEY)
        sso_url = f"https://{sso_host}{DEVICE_AUTH_ENDPOINT}"
        requests_mock.post(sso_url, json=login_auth_response)
        assert InsightsAuth().request_auth() == login_auth_response

    def test_insights_request_auth_alt_sso_host(
        self, stage_sso_host, login_auth_response, faker, requests_mock
    ):
        """Testing that insights auth targets alternate sso hosts."""
        write_insights_config({CONFIG_SSO_HOST_KEY: stage_sso_host})
        sso_url = f"https://{stage_sso_host}{DEVICE_AUTH_ENDPOINT}"
        requests_mock.post(sso_url, json=login_auth_response)
        assert InsightsAuth().request_auth() == login_auth_response

    def test_insights_request_auth_connection_error(self, stage_sso_host):
        """Testing that insights auth handles connection errors."""
        write_insights_config({CONFIG_SSO_HOST_KEY: stage_sso_host})
        with pytest.raises(InsightsAuthError) as err:
            InsightsAuth().request_auth()
            assert "Failed to request login authorization" in err.value

    def test_insights_wait_for_authorization_authorized(
        self, login_auth_response, auth_token, requests_mock
    ):
        """Testing that insights wait for authorization returns the auth token."""
        insights_auth = InsightsAuth()
        insights_auth.auth_request = login_auth_response
        sso_host = read_insights_config().get(CONFIG_SSO_HOST_KEY)
        sso_token_url = f"https://{sso_host}{TOKEN_ENDPOINT}"
        token_response = {"access_token": auth_token}
        requests_mock.post(sso_token_url, json=token_response)
        assert insights_auth.wait_for_authorization() == auth_token

    def test_insights_wait_for_authorization_authorized_alt_sso_host(
        self, stage_sso_host, login_auth_response, auth_token, requests_mock
    ):
        """Testing that insights wait for authorization handles connection errors."""
        write_insights_config({CONFIG_SSO_HOST_KEY: stage_sso_host})
        insights_auth = InsightsAuth()
        insights_auth.auth_request = login_auth_response
        sso_token_url = f"https://{stage_sso_host}{TOKEN_ENDPOINT}"
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
            assert "Failed to verify Login authorization" in err.value

    def test_insights_wait_for_authorization_bad_request(
        self, login_auth_response, auth_token, requests_mock
    ):
        """Testing that wait for authorization fails with failed checks."""
        insights_auth = InsightsAuth()
        insights_auth.auth_request = login_auth_response
        sso_host = read_insights_config().get(CONFIG_SSO_HOST_KEY)
        sso_token_url = f"https://{sso_host}{TOKEN_ENDPOINT}"
        token_response = {"error": "unknown_error"}
        requests_mock.post(
            sso_token_url, status_code=http.HTTPStatus.BAD_REQUEST, json=token_response
        )
        with pytest.raises(InsightsAuthError) as err:
            insights_auth.wait_for_authorization()
            assert "Failed to verify Login authorization" in err.value

    @patch("time.sleep")
    def test_insights_wait_for_authorization_expired(self, faker, requests_mock):
        """Testing that authorization pending checks for expired time."""
        insights_auth = InsightsAuth()
        insights_auth.auth_request = {
            "device_code": faker.slug(),
            "user_code": faker.slug(),
            "verification_uri": faker.url(),
            "verification_uri_complete": faker.url(),
            "expires_in": 1,
            "interval": 0,
        }
        sso_host = read_insights_config().get(CONFIG_SSO_HOST_KEY)
        sso_token_url = f"https://{sso_host}{TOKEN_ENDPOINT}"
        token_response = {
            "error": "authorization_pending",
            "error_description": "The authorization request is still pending",
        }
        requests_mock.post(
            sso_token_url, status_code=http.HTTPStatus.BAD_REQUEST, json=token_response
        )
        with pytest.raises(InsightsAuthError) as err:
            insights_auth.wait_for_authorization()
            assert "Time-out while waiting for Login authorization" in err.value

    def test_insights_wait_for_authorization_expired_from_sso(
        self, login_auth_response, requests_mock
    ):
        """Testing that token authorization expired from the sso server."""
        insights_auth = InsightsAuth()
        insights_auth.auth_request = login_auth_response
        sso_host = read_insights_config().get(CONFIG_SSO_HOST_KEY)
        sso_token_url = f"https://{sso_host}{TOKEN_ENDPOINT}"
        token_response = {
            "error": "expired_token",
            "error_description": "Device code is expired",
        }
        requests_mock.post(
            sso_token_url, status_code=http.HTTPStatus.BAD_REQUEST, json=token_response
        )
        with pytest.raises(InsightsAuthError) as err:
            insights_auth.wait_for_authorization()
            assert "Time-out while waiting for Login authorization" in err.value
