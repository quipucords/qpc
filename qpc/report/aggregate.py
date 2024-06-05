"""ReportAggregateCommand retrieves and outputs the aggregate report."""

import sys
from logging import getLogger

from requests import codes

from qpc import messages, report, scan
from qpc.clicommand import CliCommand
from qpc.request import GET, request
from qpc.translation import _
from qpc.utils import pretty_format

logger = getLogger(__name__)


class ReportAggregateCommand(CliCommand):
    """Defines the command for showing the aggregate report."""

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.AGGREGATE

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
        self.report_id = None

    def _validate_args(self):
        CliCommand._validate_args(self)

        if not (report_id := self.args.report_id):
            response = request(
                parser=self.parser,
                method=GET,
                path=f"{scan.SCAN_JOB_URI}{self.args.scan_job_id}",
                payload=None,
            )
            if response.status_code == codes.ok:
                json_data = response.json()
                if not (report_id := json_data.get("report_id")):
                    logger.error(
                        _(messages.REPORT_NO_AGGREGATE_REPORT_FOR_SJ),
                        self.args.scan_job_id,
                    )
                    sys.exit(1)
            else:
                logger.error(
                    _(messages.REPORT_SJ_DOES_NOT_EXIST), self.args.scan_job_id
                )
                sys.exit(1)

        self.report_id = report_id
        self.req_path = f"{self.req_path}{self.report_id}{report.AGGREGATE_PATH_SUFFIX}"

    def _handle_response_success(self):
        json_data = self.response.json()
        data = pretty_format(json_data)
        print(data)

    def _handle_response_error(self):
        if self.args.report_id is None:
            logger.error(
                _(messages.REPORT_NO_AGGREGATE_REPORT_FOR_SJ),
                self.args.scan_job_id,
            )
        else:
            logger.error(
                _(messages.REPORT_NO_AGGREGATE_REPORT_FOR_REPORT_ID),
                self.args.report_id,
            )
        sys.exit(1)
