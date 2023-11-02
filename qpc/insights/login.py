"""InsightsLoginCommand is used to save an insights user authentication token."""

from logging import getLogger

from qpc import insights, messages
from qpc.clicommand import CliCommand
from qpc.exceptions import QPCError
from qpc.translation import _
from qpc.utils import write_insights_auth_token

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
        """Persist insights login configuration."""
        user_token = None
        try:
            write_insights_auth_token(user_token)
        except QPCError as err:
            logger.error(_(err.message))
            SystemExit(1)
        logger.info(_(messages.INSIGHTS_LOGIN_CONFIG_SUCCESS))
