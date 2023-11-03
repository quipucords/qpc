"""Insights Auth is used to handle the Insights authentication workflow."""

import http
import time

import requests
from requests.exceptions import BaseHTTPError

from qpc.insights.exceptions import InsightsAuthError
from qpc.translation import _

DISCOVERY_CLIENT_ID = "discovery-client-id"
INSIGHTS_SSO_SERVER = "sso.redhat.com"
INSIGHTS_REALM = "redhat-external"
INSIGHTS_SCOPE = "api.console"
GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
DEVICE_AUTH_ENDPOINT = (
    f"/auth/realms/{INSIGHTS_REALM}/protocol/openid-connect/auth/device"
)
TOKEN_ENDPOINT = f"/auth/realms/{INSIGHTS_REALM}/protocol/openid-connect/token"


class InsightsAuth:
    """Implement the Insights Device Authorization workflow."""

    def __init__(self):
        self.auth_request = None
        self.token_response = None
        self.auth_token = None

    def request_auth(self):
        """Initialize a device authorization workflow request.

        :returns: authorization request object
        """
        self.auth_request = None

        url = f"https://{INSIGHTS_SSO_SERVER}/{DEVICE_AUTH_ENDPOINT}"  # Always SSL
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "grant_type": GRANT_TYPE,
            "scope": INSIGHTS_SCOPE,
            "client_id": DISCOVERY_CLIENT_ID,
        }
        try:
            response = requests.post(url, headers=headers, data=params)
        except BaseHTTPError as err:
            raise InsightsAuthError(
                _("Failed to request login authorization - %s"), err.message
            )

        if response.status_code == http.HTTPStatus.OK:
            self.auth_request = response.json()
        else:
            raise InsightsAuthError(
                _("Failed to request login authorization - %s"), response.reason
            )

        return self.auth_request

    def wait_for_authorization(self):
        """Wait for the user to log in and authorize the request.

        :returns: user JWT token
        """
        if self.auth_request:
            device_code = self.auth_request["device_code"]
            interval = self.auth_request.get("interval") or 5  # SSO default
            expires_in = self.auth_request.get("expires_in") or 600  # SSO default

            elapsed_time = 0
            self.auth_token = None
            while not self.auth_token:
                url = f"https://{INSIGHTS_SSO_SERVER}/{TOKEN_ENDPOINT}"  # Always SSL
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                params = {
                    "grant_type": GRANT_TYPE,
                    "client_id": DISCOVERY_CLIENT_ID,
                    "device_code": device_code,
                }
                try:
                    response = requests.post(url, headers=headers, data=params)
                except BaseHTTPError as err:
                    raise InsightsAuthError(
                        _("Failed to verify login authorization - %s"), err.message
                    )

                if response.status_code == http.HTTPStatus.OK:
                    self.token_response = response.json()
                    self.auth_token = self.token_response["access_token"]
                    break
                if response.status_code == http.HTTPStatus.BAD_REQUEST:
                    self.token_response = response.json()
                    if self.token_response.get("error") != "authorization_pending":
                        raise InsightsAuthError(
                            _("Failed to verify login authorization - %s"),
                            response.reason,
                        )
                else:
                    raise InsightsAuthError(
                        _("Failed to verify login authorization - %s"), response.reason
                    )

                time.sleep(interval)
                elapsed_time += interval
                if elapsed_time > expires_in:
                    raise InsightsAuthError(
                        _("Time-out while waiting for login authorization")
                    )

        return self.auth_token
