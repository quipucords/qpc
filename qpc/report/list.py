"""ReportListCommand is used to list available reports."""

import json
from logging import getLogger

from requests import codes

from qpc import report
from qpc.clicommand import CliCommand
from qpc.request import GET
from qpc.utils import pretty_format

logger = getLogger(__name__)

MIN_SERVER_VERSION = "2.4.3"


class ReportListCommand(CliCommand):
    """Defines the report list command.

    This command is for listing available reports.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.LIST

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

        self.min_server_version = MIN_SERVER_VERSION

    def _validate_args(self):  # noqa: PLR0912
        CliCommand._validate_args(self)
        self.req_headers = {"Accept": "application/json"}
        self.req_path = f"{self.req_path}"

    def _handle_response_success(self):
        json_data = json.loads(self.response.text)
        response_json = pretty_format(json_data)
        print(response_json)
