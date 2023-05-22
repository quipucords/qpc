"""ReportInsightsCommand is to show insights report."""

import sys
from logging import getLogger

from requests import codes

from qpc import messages, report, scan
from qpc.clicommand import CliCommand
from qpc.request import GET, request
from qpc.translation import _
from qpc.utils import check_extension, validate_write_file, write_file

logger = getLogger(__name__)


# pylint: disable=too-few-public-methods
class ReportInsightsCommand(CliCommand):
    """Defines the report insights command.

    This command is for showing the insights report.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.INSIGHTS

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            GET,
            report.REPORT_URI,
            [codes.ok],
        )
        id_group = self.parser.add_mutually_exclusive_group(required=True)
        id_group.add_argument(
            "--scan-job",
            dest="scan_job_id",
            metavar="SCAN_JOB_ID",
            help=_(messages.REPORT_SCAN_JOB_ID_HELP),
        )
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
        # Don't change this when you upgrade versions
        self.min_server_version = "0.9.0"
        self.report_id = None

    def _validate_args(self):
        CliCommand._validate_args(self)
        if self.args.path:
            self.req_headers = {"Accept": "application/gzip"}
        else:
            self.req_headers = {"Accept": "application/json"}
        check_extension("tar.gz", self.args.path)

        try:
            if self.args.path:
                validate_write_file(self.args.path, "output-file")
        except ValueError as error:
            logger.error(error)
            sys.exit(1)

        if self.args.report_id is None:
            # Lookup scan job id
            response = request(
                parser=self.parser,
                method=GET,
                path=f"{scan.SCAN_JOB_URI}{self.args.scan_job_id}",
                payload=None,
            )
            if response.status_code == codes.ok:  # pylint: disable=no-member
                json_data = response.json()
                self.report_id = json_data.get("report_id")
                if self.report_id:
                    self.req_path = (
                        f"{self.req_path}{self.report_id}{report.INSIGHTS_PATH_SUFFIX}"
                    )
                else:
                    logger.error(
                        _(messages.REPORT_NO_INSIGHTS_REPORT_FOR_SJ),
                        self.args.scan_job_id,
                    )
                    sys.exit(1)
            else:
                logger.error(
                    _(messages.REPORT_SJ_DOES_NOT_EXIST), self.args.scan_job_id
                )
                sys.exit(1)
        else:
            self.report_id = self.args.report_id
            self.req_path = (
                f"{self.req_path}{self.report_id}{report.INSIGHTS_PATH_SUFFIX}"
            )

    def _handle_response_success(self):
        try:
            if self.args.path:
                file_content = self.response.content
            else:
                file_content = self.response.text
            write_file(self.args.path, file_content, binary=True)
            logger.info(_(messages.REPORT_SUCCESSFULLY_WRITTEN))
        except EnvironmentError as err:
            logger.error(
                _(messages.WRITE_FILE_ERROR), {"path": self.args.path, "error": err}
            )
            sys.exit(1)

    def _handle_response_error(self):  # pylint: disable=arguments-differ
        if self.args.report_id is None:
            logger.error(
                _(messages.REPORT_NO_INSIGHTS_REPORT_FOR_SJ), self.args.scan_job_id
            )
        else:
            logger.error(
                _(messages.REPORT_NO_INSIGHTS_REPORT_FOR_REPORT_ID), self.args.report_id
            )
        sys.exit(1)
