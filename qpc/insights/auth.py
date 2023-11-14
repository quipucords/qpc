"""Insights Auth is used to handle the Insights authentication workflow."""

import http
import time
from logging import getLogger

import requests
from requests.exceptions import BaseHTTPError, ConnectionError

from qpc import messages
from qpc.insights.exceptions import InsightsAuthError
from qpc.translation import _
from qpc.utils import CONFIG_SSO_HOST_KEY, read_insights_config

logger = getLogger(__name__)

DISCOVERY_CLIENT_ID = "discovery-client-id"
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

        config = read_insights_config()
        insights_sso_server = config.get(CONFIG_SSO_HOST_KEY)
        url = f"https://{insights_sso_server}{DEVICE_AUTH_ENDPOINT}"  # Always SSL
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "grant_type": GRANT_TYPE,
            "scope": INSIGHTS_SCOPE,
            "client_id": DISCOVERY_CLIENT_ID,
        }
        try:
            logger.info(_(messages.INSIGHTS_LOGIN_REQUEST), url)
            response = requests.post(url, headers=headers, data=params)
        except ConnectionError as err:
            raise InsightsAuthError(_(messages.INSIGHTS_LOGIN_REQUEST_FAILED % err))
        except BaseHTTPError as err:
            raise InsightsAuthError(_(messages.INSIGHTS_LOGIN_REQUEST_FAILED % err))

        if response.status_code == http.HTTPStatus.OK:
            self.auth_request = response.json()
            logger.debug(
                _(messages.INSIGHTS_RESPONSE), insights_sso_server, self.auth_request
            )
        else:
            logger.debug(
                _(messages.INSIGHTS_RESPONSE), insights_sso_server, response.text
            )
            raise InsightsAuthError(
                _(messages.INSIGHTS_LOGIN_REQUEST_FAILED % response.reason)
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
                config = read_insights_config()
                insights_sso_server = config.get(CONFIG_SSO_HOST_KEY)
                url = f"https://{insights_sso_server}{TOKEN_ENDPOINT}"  # Always SSL
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                params = {
                    "grant_type": GRANT_TYPE,
                    "client_id": DISCOVERY_CLIENT_ID,
                    "device_code": device_code,
                }
                try:
                    logger.debug(_(messages.INSIGHTS_LOGIN_VERIFYING), url)
                    response = requests.post(url, headers=headers, data=params)
                except ConnectionError as err:
                    raise InsightsAuthError(
                        _(messages.INSIGHTS_LOGIN_VERIFICATION_FAILED % err)
                    )
                except BaseHTTPError as err:
                    raise InsightsAuthError(
                        _(messages.INSIGHTS_LOGIN_VERIFICATION_FAILED % err)
                    )

                if response.status_code == http.HTTPStatus.OK:
                    self.token_response = response.json()
                    self.auth_token = self.token_response["access_token"]
                    break
                if response.status_code == http.HTTPStatus.BAD_REQUEST:
                    self.token_response = response.json()
                    if self.token_response.get("error") != "authorization_pending":
                        logger.debug(
                            _(messages.INSIGHTS_RESPONSE),
                            insights_sso_server,
                            response.text,
                        )
                        raise InsightsAuthError(
                            _(
                                messages.INSIGHTS_LOGIN_VERIFICATION_FAILED
                                % response.reason
                            )
                        )
                    else:
                        logger.debug(
                            _(messages.INSIGHTS_RESPONSE),
                            insights_sso_server,
                            self.token_response,
                        )
                else:
                    logger.debug(
                        _(messages.INSIGHTS_RESPONSE),
                        insights_sso_server,
                        response.text,
                    )
                    raise InsightsAuthError(
                        _(messages.INSIGHTS_LOGIN_VERIFICATION_FAILED % response.reason)
                    )

                time.sleep(interval)
                elapsed_time += interval
                if elapsed_time > expires_in:
                    raise InsightsAuthError(
                        _(messages.INSIGHTS_LOGIN_VERIFICATION_TIMEOUT)
                    )

        return self.auth_token
