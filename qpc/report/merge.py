"""ReportMergeCommand is used to merge scan jobs results."""

import json
import sys
from logging import getLogger
from pathlib import Path

from requests import codes

from qpc import messages, report
from qpc.clicommand import CliCommand
from qpc.release import QPC_VAR_PROGRAM_NAME
from qpc.report import utils
from qpc.request import GET, POST, PUT, request
from qpc.scan import SCAN_JOB_URI
from qpc.translation import _

logger = getLogger(__name__)


try:
    json_exception_class = json.decoder.JSONDecodeError
except AttributeError:
    json_exception_class = ValueError


class ReportMergeCommand(CliCommand):
    """Defines the report merge command.

    This command is for merging scan job results into a
    single report.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.MERGE

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            PUT,
            report.ASYNC_MERGE_URI,
            [codes.created],
        )
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--job-ids",
            dest="scan_job_ids",
            nargs="+",
            metavar="SCAN_JOB_IDS",
            default=[],
            help=_(messages.REPORT_SCAN_JOB_IDS_HELP),
        )
        group.add_argument(
            "--report-ids",
            dest="report_ids",
            nargs="+",
            metavar="REPORT_IDS",
            default=[],
            help=_(messages.REPORT_REPORT_IDS_HELP),
        )
        group.add_argument(
            "--json-files",
            dest="json_files",
            nargs="+",
            metavar="JSON_FILES",
            default=[],
            help=_(messages.REPORT_JSON_FILE_HELP),
        )
        group.add_argument(
            "--json-directory",
            dest="json_dir",
            nargs="+",
            help=_(messages.REPORT_JSON_DIR_HELP),
        )
        self.json = None
        self.report_ids = None

    def _get_report_ids(self):
        """Grab the report ids from the scan job if it exists.

        :returns Boolean regarding the existence of scan jobs &
        the report ids
        """
        not_found = False
        report_ids = []
        job_not_found = []
        report_not_found = []
        for scan_job_id in set(self.args.scan_job_ids):
            # check for existence of scan_job
            path = SCAN_JOB_URI + str(scan_job_id) + "/"
            response = request(
                parser=self.parser, method=GET, path=path, params=None, payload=None
            )
            if response.status_code == codes.ok:
                json_data = response.json()
                report_id = json_data.get("report_id", None)
                if report_id:
                    report_ids.append(report_id)
                else:
                    # there is not a report id associated with this scan job
                    report_not_found.append(scan_job_id)
                    not_found = True
            else:
                job_not_found.append(scan_job_id)
                not_found = True
        return not_found, report_ids, job_not_found, report_not_found

    def _validate_create_json(self, files):
        """Validate the set of files to be merged.

        :param files: list(str) of the files to be merged
        """
        logger.info(_(messages.REPORT_VALIDATE_JSON), files)
        all_sources = []
        for file in files:
            sources = utils.validate_and_create_json(file)
            # Source is valid so add it
            if sources:
                all_sources += sources
        if all_sources == []:
            logger.error(_(messages.REPORT_JSON_DIR_ALL_FAIL))
            sys.exit(1)
        self.json = {
            utils.SOURCES_KEY: all_sources,
            utils.REPORT_TYPE_KEY: utils.DETAILS_REPORT_TYPE,
        }

    def _merge_json(self):
        """Combine the sources for each json file provided.

        :returns Json containing the sources of each file.
        """
        if len(self.args.json_files) > 1:
            self._validate_create_json(self.args.json_files)
        else:
            logger.error(_(messages.REPORT_JSON_FILES_HELP))
            sys.exit(1)

    def _merge_json_dir(self):
        """Combine the sources for each json file in a directory.

        :returns Json containing the sources of each file.
        """
        path = self.args.json_dir
        if isinstance(path, list):
            path = path[0]
        path = Path(path)
        if not path.is_dir():
            logger.error(_(messages.REPORT_JSON_DIR_NOT_FOUND), path)
            sys.exit(1)
        json_files = list(path.glob("*.json"))
        if not json_files:
            logger.error(_(messages.REPORT_JSON_DIR_NO_FILES), path)
            sys.exit(1)
        self._validate_create_json(json_files)

    def _validate_args(self):
        CliCommand._validate_args(self)
        report_ids = []
        if self.args.scan_job_ids:
            # check for existence of jobs & get report ids
            (
                not_found,
                report_ids,
                job_not_found,
                report_not_found,
            ) = self._get_report_ids()
            if not_found is True:
                if job_not_found:
                    logger.error(_(messages.REPORT_SJS_DO_NOT_EXIST), job_not_found)
                if report_not_found:
                    logger.error(
                        _(messages.REPORTS_REPORTS_DO_NOT_EXIST), report_not_found
                    )
                sys.exit(1)
        elif self.args.report_ids:
            report_ids = self.args.report_ids
        elif self.args.json_files:
            self._merge_json()
        elif self.args.json_dir:
            self._merge_json_dir()
        self.report_ids = report_ids

    def _build_data(self):
        """Construct the payload for a merging reports.

        :returns: a dictionary representing the jobs to merge
        """
        if self.args.json_files or self.args.json_dir:
            self.req_method = POST
            self.req_payload = self.json
        else:
            self.req_method = PUT
            self.req_payload = {
                "reports": self.report_ids,
            }

    def _handle_response_success(self):
        json_data = self.response.json()
        if json_data.get("id"):
            print(
                _(messages.REPORT_SUCCESSFULLY_MERGED)
                % {"id": json_data.get("id"), "prog_name": QPC_VAR_PROGRAM_NAME},
            )

    def _handle_response_error(self):
        json_data = self.response.json()
        reports = json_data.get("reports")
        if reports:
            logger.error(json_data.get("reports")[0])
            sys.exit(1)

        logger.error(_(messages.MERGE_ERROR), json_data)
        sys.exit(1)
