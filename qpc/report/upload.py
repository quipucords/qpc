"""ReportUploadCommand is used to upload details JSON."""

import json
import sys
from logging import getLogger

from requests import codes

from qpc import messages, report
from qpc.clicommand import CliCommand
from qpc.release import PKG_NAME
from qpc.report import utils
from qpc.request import POST
from qpc.translation import _

logger = getLogger(__name__)


# pylint: disable=invalid-name
try:
    json_exception_class = json.decoder.JSONDecodeError
except AttributeError:
    json_exception_class = ValueError
# pylint: disable=too-few-public-methods


class ReportUploadCommand(CliCommand):
    """Defines the report upload command.

    This command is for uploading a details json report
    to produce a deployment report.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.UPLOAD

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            POST,
            report.ASYNC_MERGE_URI,
            [codes.created],
        )
        self.parser.add_argument(
            "--json-file",
            dest="json_file",
            metavar="JSON_FILE",
            help=_(messages.REPORT_UPLOAD_JSON_FILE_HELP),
            required=True,
        )
        self.json = None

    def _validate_create_json(self, file):
        """Validate the details report file to be uploaded.

        :param files: str containing path for details report file
        """
        sources = utils.validate_and_create_json(file)

        if not sources:
            logger.error(_(messages.REPORT_UPLOAD_FILE_INVALID_JSON), file)
            sys.exit(1)
        self.json = {
            utils.SOURCES_KEY: sources,
            utils.REPORT_TYPE_KEY: utils.DETAILS_REPORT_TYPE,
        }

    def _validate_args(self):
        CliCommand._validate_args(self)
        if self.args.json_file:
            self._validate_create_json(self.args.json_file)

    def _build_data(self):
        """Construct the payload for a merging reports.

        :returns: a dictionary representing the jobs to merge
        """
        self.req_method = POST
        self.req_payload = self.json

    def _handle_response_success(self):
        json_data = self.response.json()
        if json_data.get("id"):
            logger.info(
                _(messages.REPORT_SUCCESSFULLY_UPLOADED),
                {"id": json_data.get("id"), "pkg_name": PKG_NAME}
            )

    def _handle_response_error(self):  # pylint: disable=arguments-differ
        json_data = self.response.json()
        logger.error(_(messages.REPORT_FAILED_TO_UPLOADED), json_data.get("error"))
        sys.exit(1)
