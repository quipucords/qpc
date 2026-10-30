"""LightspeedLoginCommand is used to save a lightspeed user authentication token."""

from logging import getLogger

from qpc import lightspeed
from qpc.clicommand import CliCommand
from qpc.lightspeed.auth import LightspeedAuth
from qpc.lightspeed.exceptions import LightspeedAuthError
from qpc.translation import _
from qpc.utils import clear_lightspeed_auth_token, write_lightspeed_auth_token

logger = getLogger(__name__)


class LightspeedLoginCommand(CliCommand):
    """Define lightspeed login command.

    This command is for getting a lightspeed user authentication token
    """

    SUBCOMMAND = lightspeed.SUBCOMMAND
    ACTION = lightspeed.LOGIN

    def __init__(self, subparsers):
        """Create command."""
        super().__init__(
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            None,
            None,
            [],
        )

    def _do_command(self):
        """Request Lightspeed login authorization."""
        auth_token = None
        try:
            clear_lightspeed_auth_token()
            lightspeed_auth = LightspeedAuth()
            auth_request = lightspeed_auth.request_auth()
            print("Lightspeed login authorization requested")
            print(f"User Code: {auth_request['user_code']}")
            print(f"Authorization URL: {auth_request['verification_uri_complete']}")
            print("Waiting for login authorization ...")
            auth_token = lightspeed_auth.wait_for_authorization()
            print("Login authorization successful.")
            write_lightspeed_auth_token(auth_token)
        except LightspeedAuthError as err:
            logger.error(_(err.message))
            raise SystemExit(1)
