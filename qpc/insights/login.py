"""InsightsLoginCommand is used to save an insights user authentication token."""

from logging import getLogger

from qpc import insights
from qpc.clicommand import CliCommand
from qpc.insights.auth import InsightsAuth
from qpc.insights.exceptions import InsightsAuthError
from qpc.translation import _
from qpc.utils import clear_insights_auth_token, write_insights_auth_token

logger = getLogger(__name__)


class InsightsLoginCommand(CliCommand):
    """Define insights login command.

    This command is for getting an insights user authentication token
    """

    SUBCOMMAND = insights.SUBCOMMAND
    ACTION = insights.LOGIN

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
        """Request Insights login authorization."""
        auth_token = None
        try:
            clear_insights_auth_token()
            insights_auth = InsightsAuth()
            auth_request = insights_auth.request_auth()
            print("Insights login authorization requested")
            print(f"User Code: {auth_request['user_code']}")
            print(f"Authorization URL: {auth_request['verification_uri_complete']}")
            print("Waiting for login authorization ...")
            auth_token = insights_auth.wait_for_authorization()
            print("Login authorization successful.")
            write_insights_auth_token(auth_token)
        except InsightsAuthError as err:
            logger.error(_(err.message))
            SystemExit(1)
