"""LogoutHostCommand is used to remove any existing login token."""

from logging import getLogger

from requests import codes

from qpc import messages, server
from qpc.clicommand import CliCommand
from qpc.request import PUT
from qpc.translation import _
from qpc.utils import delete_client_token

logger = getLogger(__name__)


class LogoutHostCommand(CliCommand):
    """Defines the logout host command.

    This command is for logging out of theserver for the CLI.
    """

    SUBCOMMAND = server.SUBCOMMAND
    ACTION = server.LOGOUT

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            PUT,
            server.LOGOUT_URI,
            [codes.ok],
        )

    def _handle_response_success(self):
        """Remove the client token."""
        delete_client_token()
        logger.info(_(messages.LOGOUT_SUCCESS))
