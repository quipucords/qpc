"""ScanStartCommand is used to trigger a host scan."""

import sys
from logging import getLogger

from requests import codes

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import POST
from qpc.scan.utils import get_scan_object_id
from qpc.translation import _

logger = getLogger(__name__)


class ScanStartCommand(CliCommand):
    """Defines the start command.

    This command is for triggering host scans with a source to gather system
    facts.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.START

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            POST,
            scan.SCAN_URI,
            [codes.created],
        )
        self.parser.add_argument(
            "--name",
            dest="name",
            metavar="NAME",
            help=_(messages.SCAN_NAME_HELP),
            required=True,
        )

    def _validate_args(self):
        CliCommand._validate_args(self)
        if self.args.name:
            # check for existence of scan object
            found, scan_object_id = get_scan_object_id(self.parser, self.args.name)
            if found is False:
                sys.exit(1)
            else:
                self.req_path = scan.SCAN_URI + scan_object_id + "jobs/"

    def _handle_response_success(self):
        json_data = self.response.json()
        print(_(messages.SCAN_STARTED) % json_data.get("id"))
