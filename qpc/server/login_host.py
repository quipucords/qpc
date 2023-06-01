"""LoginHostCommand is used to login with username and password."""

from getpass import getpass
from logging import getLogger

from requests import codes

from qpc import messages, server
from qpc.clicommand import CliCommand
from qpc.request import POST
from qpc.translation import _
from qpc.utils import delete_client_token, write_client_token

logger = getLogger(__name__)


class LoginHostCommand(CliCommand):
    """Defines the login host command.

    This command is for logging into the target
    host for the CLI.
    """

    SUBCOMMAND = server.SUBCOMMAND
    ACTION = server.LOGIN

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            POST,
            server.LOGIN_URI,
            [codes.ok],
        )

        self.parser.add_argument(
            "--username",
            dest="username",
            metavar="USERNAME",
            help=_(messages.LOGIN_USER_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--password",
            dest="password",
            metavar="PASSWORD",
            help=_(messages.LOGIN_PASS_HELP),
            required=False,
        )
        self.username = None
        self.password = None

    def _validate_args(self):
        CliCommand._validate_args(self)

        delete_client_token()
        if "username" in self.args and self.args.username:
            # check for file existence on system
            self.username = self.args.username
        else:
            self.username = input(_(messages.LOGIN_USERNAME_PROMPT))

        if "password" in self.args and self.args.password:
            self.password = self.args.password
        else:
            self.password = getpass()

    def _build_data(self):
        """Construct the dictionary credential given our arguments.

        :returns: a dictionary representing the credential being added
        """
        self.req_payload = {"username": self.username, "password": self.password}

    def _handle_response_success(self):
        json_data = self.response.json()
        write_client_token(json_data)
        logger.info(_(messages.LOGIN_SUCCESS))
