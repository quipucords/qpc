"""ReportShowCommand is used to show an individual report."""

import json
import sys
from logging import getLogger

from requests import codes

from qpc import messages, report
from qpc.clicommand import CliCommand
from qpc.request import GET
from qpc.translation import _
from qpc.utils import (
    check_extension,
    pretty_format,
    validate_write_file,
    write_file,
)

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

        self.parser.add_argument(
            "--output-file",
            dest="path",
            metavar="PATH",
            help=_(messages.REPORT_PATH_HELP),
        )
        self.report_id = None
        self.min_server_version = MIN_SERVER_VERSION

    def _validate_args(self):  # noqa: PLR0912
        CliCommand._validate_args(self)
        extension = ".json"
        self.req_headers = {"Accept": "application/json"}
        check_extension(extension, self.args.path)
        try:
            if self.args.path:
                validate_write_file(self.args.path, "output-file")
        except ValueError as error:
            logger.error(error)
            sys.exit(1)

        self.report_id = self.args.report_id
        self.req_path = f"{self.req_path}{self.report_id}/"

    def _handle_response_success(self):
        try:
            json_data = json.loads(self.response.text)
            response_json = pretty_format(json_data)
            write_file(self.args.path, response_json)
            logger.info(_(messages.REPORT_SUCCESSFULLY_WRITTEN))
        except EnvironmentError as err:
            logger.error(
                _(messages.WRITE_FILE_ERROR), {"path": self.args.path, "error": err}
            )
            sys.exit(1)

    def _handle_response_error(self):
        logger.error(_(messages.REPORT_ID_DOES_NOT_EXIST), self.args.report_id)
        sys.exit(1)
