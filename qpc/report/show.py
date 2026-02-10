"""ReportShowCommand is used to show an individual report."""

import json
import sys
from logging import getLogger

from requests import codes

from qpc import messages, report
from qpc.clicommand import CliCommand
from qpc.request import GET
from qpc.translation import _
from qpc.utils import pretty_format

logger = getLogger(__name__)

MIN_SERVER_VERSION = "2.4.3"


class ReportShowCommand(CliCommand):
    """Defines the report show command.

    This command is for showing an individual report.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.SHOW

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            GET,
            report.REPORT_V2_URI,
            [codes.ok],
        )
        id_group = self.parser.add_mutually_exclusive_group(required=True)
        id_group.add_argument(
            "--report",
            dest="report_id",
            metavar="REPORT_ID",
            help=_(messages.REPORT_REPORT_ID_HELP),
        )

        self.report_id = None
        self.min_server_version = MIN_SERVER_VERSION

    def _validate_args(self):  # noqa: PLR0912
        CliCommand._validate_args(self)
        self.req_headers = {"Accept": "application/json"}
        self.report_id = self.args.report_id
        self.req_path = f"{self.req_path}{self.report_id}/"

    def _handle_response_success(self):
        json_data = json.loads(self.response.text)
        response_json = pretty_format(json_data)
        print(response_json)

    def _handle_response_error(self):
        logger.error(_(messages.REPORT_ID_DOES_NOT_EXIST), self.args.report_id)
        sys.exit(1)
