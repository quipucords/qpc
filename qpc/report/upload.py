#!/usr/bin/env python
#
# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""ReportUploadCommand is used to upload details JSON."""

from __future__ import print_function

import json
import sys

from qpc import messages, report
from qpc.clicommand import CliCommand
from qpc.release import PKG_NAME
from qpc.report import utils
from qpc.request import POST
from qpc.translation import _

from requests import codes

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
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), POST,
                            report.ASYNC_MERGE_URI, [codes.created])
        self.parser.add_argument('--json-file', dest='json_file',
                                 metavar='JSON_FILE',
                                 help=_(messages.REPORT_UPLOAD_JSON_FILE_HELP),
                                 required=True)
        self.json = None

    def _validate_create_json(self, file):
        """Validate the details report file to be uploaded.

        :param files: str containing path for details report file
        """
        sources = utils.validate_and_create_json(file)

        if not sources:
            print(_(messages.REPORT_UPLOAD_FILE_INVALID_JSON) % file)
            sys.exit(1)
        self.json = {utils.SOURCES_KEY: sources,
                     utils.REPORT_TYPE_KEY: utils.DETAILS_REPORT_TYPE}

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
        if json_data.get('id'):
            print(_(messages.REPORT_SUCCESSFULLY_UPLOADED % (
                json_data.get('id'),
                PKG_NAME,
                json_data.get('id'))))

    def _handle_response_error(self):
        json_data = self.response.json()
        print(_(messages.REPORT_FAILED_TO_UPLOADED) % json_data.get('error'))
        sys.exit(1)
