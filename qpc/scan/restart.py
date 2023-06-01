"""ScanRestartCommand is used to restart a specific system scan."""

from logging import getLogger

from requests import codes

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import PUT
from qpc.translation import _

logger = getLogger(__name__)


class ScanRestartCommand(CliCommand):
    """Defines the restart command.

    This command is for restarting a specific scan to gather facts.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.RESTART

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            PUT,
            scan.SCAN_JOB_URI,
            [codes.ok],
        )
        self.parser.add_argument(
            "--id",
            dest="id",
            metavar="ID",
            help=_(messages.SCAN_JOB_ID_HELP),
            required=True,
        )

    def _validate_args(self):
        CliCommand._validate_args(self)
        if self.args.id:
            self.req_path = self.req_path + str(self.args.id) + "/restart/"

    def _handle_response_success(self):
        logger.info(_(messages.SCAN_RESTARTED), self.args.id)
