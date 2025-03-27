"""ScanCancelCommand is used to cancel a specific system scan."""

from logging import getLogger

from requests import codes

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import PUT
from qpc.translation import _

logger = getLogger(__name__)


class ScanCancelCommand(CliCommand):
    """Defines the cancel command.

    This command is for cancel a specific scan to gather facts.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.CANCEL

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            PUT,
            scan.SCAN_JOB_V1_URI,
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
            self.req_path = self.req_path + str(self.args.id) + "/cancel/"

    def _handle_response_success(self):
        logger.info(_(messages.SCAN_CANCELED), self.args.id)
