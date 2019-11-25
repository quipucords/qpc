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
"""ReportValidateCommand is used to validate a report against it's hash."""

from __future__ import print_function

import json
import os

from qpc import messages, report
from qpc.clicommand import CliCommand
from qpc.request import PUT
from qpc.translation import _

from requests import codes

# pylint: disable=invalid-name
try:
    json_exception_class = json.decoder.JSONDecodeError
except AttributeError:
    json_exception_class = ValueError
# pylint: disable=too-few-public-methods


class ReportValidateCommand(CliCommand):
    """Defines the report validate command.

    This command is for validating a report against it's hash.
    """

    SUBCOMMAND = report.SUBCOMMAND
    ACTION = report.VALIDATE

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), PUT,
                            report.VALIDATE_URI, [codes.created])
        self.parser.add_argument('--report-file', dest='report_file',
                                 metavar='REPORT_FILE', default=[],
                                 help=_(messages.REPORT_VALIDATE_FILE_HELP))
        self.parser.add_argument('--report-hash', dest='report_hash',
                                 help=_(messages.REPORT_VALIDATE_HASH_HELP))
        self.report = None

    def _validate_args(self):
        CliCommand._validate_args(self)
        if self.args.report_file:
            if os.path.isfile(self.args.report_file):
                with open(self.args.report_file, 'r') as file_contents:
                    try:
                        self.report = json.load(file_contents)
                    except json_exception_class:
                        self.report = file_contents.read()
                        print('the following are the contents: ')
                        print(self.report)

    def _build_data(self):
        """Construct the payload for a merging reports.

        :returns: a dictionary representing the jobs to merge
        """
        self.req_method = PUT
        self.req_payload = {
            'report': self.report,
            'hash': self.args.report_hash,
        }

    def _handle_response_success(self):
        json_data = self.response.json()
        print(json_data)

    def _handle_response_error(self):
        json_data = self.response.json()
        print(json_data)
