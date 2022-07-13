"""InsightsAddLoginCommand is used to save insights login configuration."""

from logging import getLogger

from qpc import insights, messages
from qpc.clicommand import CliCommand
from qpc.insights.utils import validate_username_and_password
from qpc.translation import _
from qpc.utils import write_insights_login_config

log = getLogger("qpc")


class InsightsAddLoginCommand(CliCommand):
    """Define insights add_login command.

    This command is for storing insights
    login information, username and password
    """

    SUBCOMMAND = insights.SUBCOMMAND
    ACTION = insights.ADD_LOGIN

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
        self.parser.add_argument(
            "--username",
            dest="username",
            metavar="USERNAME",
            type=validate_username_and_password,
            help=_(messages.INSIGHTS_ADD_USERNAME_USER_HELP),
            required=True,
        )
        self.parser.add_argument(
            "--password",
            dest="password",
            type=validate_username_and_password,
            metavar="PASSWORD",
            help=_(messages.INSIGHTS_ADD_PASS_USER_HELP),
            required=True,
        )

    def _do_command(self):
        """Persist insights login configuration."""
        login_config = {
            "username": self.args.username,
            "password": self.args.password,
        }
        write_insights_login_config(login_config)
        log.info(messages.INSIGHTS_LOGIN_CONFIG_SUCCESS)
