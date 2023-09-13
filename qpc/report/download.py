"""ReportDownloadCommand is used to download all reports."""

import sys
from logging import getLogger

from requests import codes

from qpc import messages, report, scan
from qpc.clicommand import CliCommand
from qpc.request import GET, request
from qpc.translation import _
from qpc.utils import check_extension, validate_write_file, write_file

logger = getLogger(__name__)


class ReportDownloadCommand(CliCommand):
    """Defines the report download command.

    This command is for downloading all reports.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.DOWNLOAD

    def __init__(self, subparsers):
        """Create command."""
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
            help=_(messages.DOWNLOAD_PATH_HELP),
            required=True,
        )
        self.min_server_version = "0.9.2"
        self.report_id = None

    def _validate_args(self):
        self.req_headers = {"Accept": "application/gzip"}
        try:
            validate_write_file(self.args.path, "output-file")
        except ValueError as error:
            logger.error(error)
            sys.exit(1)
        check_extension("tar.gz", self.args.path)
        if self.args.report_id is None:
            # Lookup scan job id
            response = request(
                parser=self.parser,
                method=GET,
                path=f"{scan.SCAN_JOB_URI}{self.args.scan_job_id}",
                payload=None,
            )
            if response.status_code == codes.ok:
                json_data = response.json()
                self.report_id = json_data.get("report_id")
                if self.report_id:
                    self.req_path = f"{self.req_path}{self.report_id}"
                else:
                    logger.error(
                        _(messages.DOWNLOAD_NO_REPORT_FOR_SJ), self.args.scan_job_id
                    )
                    sys.exit(1)
            else:
                logger.error(
                    _(messages.DOWNLOAD_SJ_DOES_NOT_EXIST), self.args.scan_job_id
                )
                sys.exit(1)
        else:
            self.report_id = self.args.report_id
            self.req_path = f"{self.req_path}{self.report_id}"

    def _handle_response_success(self):
        file_content = self.response.content
        try:
            write_file(self.args.path, file_content, True)
            logger.info(
                _(messages.DOWNLOAD_SUCCESSFULLY_WRITTEN),
                {"report": self.report_id, "path": self.args.path},
            )
        except EnvironmentError as err:
            logger.error(
                _(messages.WRITE_FILE_ERROR), {"path": self.args.path, "error": err}
            )
            sys.exit(1)

    def _handle_response_error(self):
        logger.error(_(messages.DOWNLOAD_NO_REPORT_FOUND), self.args.report_id)
        sys.exit(1)
