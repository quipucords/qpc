#!/usr/bin/env python
#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""ReportDownloadCommand is used to download all reports."""

from __future__ import print_function

import sys

from requests import codes

from qpc import messages, report, scan
from qpc.clicommand import CliCommand
from qpc.request import GET, request
from qpc.translation import _
from qpc.utils import check_extension, validate_write_file, write_file


# pylint: disable=too-few-public-methods
class ReportDownloadCommand(CliCommand):
    """Defines the report download command.

    This command is for downloading all reports.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.DOWNLOAD

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
            help=_(messages.DOWNLOAD_PATH_HELP),
            required=True,
        )
        self.parser.add_argument(
            "--mask",
            dest="mask",
            action="store_true",
            help=_(messages.REPORT_MASK_HELP),
            required=False,
        )
        self.min_server_version = "0.9.2"
        self.report_id = None

    def _validate_args(self):
        self.req_headers = {"Accept": "application/gzip"}
        if self.args.mask:
            self.req_params = {"mask": True}
        try:
            validate_write_file(self.args.path, "output-file")
        except ValueError as error:
            print(error)
            sys.exit(1)
        check_extension("tar.gz", self.args.path)
        if self.args.report_id is None:
            # Lookup scan job id
            response = request(
                parser=self.parser,
                method=GET,
                path="%s%s" % (scan.SCAN_JOB_URI, self.args.scan_job_id),
                payload=None,
            )
            if response.status_code == codes.ok:  # pylint: disable=no-member
                json_data = response.json()
                self.report_id = json_data.get("report_id")
                if self.report_id:
                    self.req_path = "%s%s" % (self.req_path, self.report_id)
                else:
                    print(_(messages.DOWNLOAD_NO_REPORT_FOR_SJ % self.args.scan_job_id))
                    sys.exit(1)
            else:
                print(_(messages.DOWNLOAD_SJ_DOES_NOT_EXIST % self.args.scan_job_id))
                sys.exit(1)
        else:
            self.report_id = self.args.report_id
            self.req_path = "%s%s" % (self.req_path, self.report_id)

    def _handle_response_success(self):
        file_content = self.response.content
        try:
            write_file(self.args.path, file_content, True)
            print(
                _(
                    messages.DOWNLOAD_SUCCESSFULLY_WRITTEN
                    % (self.report_id, self.args.path)
                )
            )
        except EnvironmentError as err:
            err_msg = _(messages.WRITE_FILE_ERROR % (self.args.path, err))
            print(err_msg)
            sys.exit(1)

    def _handle_response_error(self):  # pylint: disable=arguments-differ
        if self.response.status_code == 428:
            print(_(messages.DOWNLOAD_NO_MASK_REPORT) % self.args.report_id)
        else:
            print(_(messages.DOWNLOAD_NO_REPORT_FOUND % self.args.report_id))
        sys.exit(1)
