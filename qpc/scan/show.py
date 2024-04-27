"""ScanShowCommand is used to show info on a specific system scan."""

import sys
from logging import getLogger

from requests import codes

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import GET, request
from qpc.translation import _
from qpc.utils import pretty_format

logger = getLogger(__name__)


class ScanShowCommand(CliCommand):
    """Defines the show command.

    This command is for showing the status of a specific scan
    to gather facts.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.SHOW

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            GET,
            scan.SCAN_URI,
            [codes.ok],
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
        found = False
        response = request(
            parser=self.parser,
            method=GET,
            path=scan.SCAN_URI,
            params={"name": self.args.name},
            payload=None,
        )
        if response.status_code == codes.ok:
            json_data = response.json()
            count = json_data.get("count", 0)
            results = json_data.get("results", [])
            if count >= 1:
                for result in results:
                    if result["name"] == self.args.name:
                        self.req_path = self.req_path + str(result["id"]) + "/"
                        found = True
            if not found or count == 0:
                logger.error(_(messages.SCAN_DOES_NOT_EXIST), self.args.name)
                sys.exit(1)

    def _handle_response_success(self):
        json_data = self.response.json()
        data = pretty_format(json_data)
        print(data)

    def _handle_response_error(self):
        logger.error(_(messages.SCAN_DOES_NOT_EXIST), self.args.name)
        sys.exit(1)
