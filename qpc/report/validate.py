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
import sys

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
                            report.VALIDATE_URI, [codes.ok])
        required_args = self.parser.add_argument_group('required arguments')
        required_args.add_argument('--report', dest='report_file',
                                   metavar='REPORT_FILE', default=[],
                                   help=_(messages.REPORT_VALIDATE_FILE_HELP),
                                   required=True)
        required_args.add_argument('--hash', dest='report_hash',
                                   help=_(messages.REPORT_VALIDATE_HASH_HELP),
                                   required=True)
        self.report = None

    def _validate_args(self):
        """Validate the report file."""
        CliCommand._validate_args(self)
        if self.args.report_file:
            if os.path.isfile(self.args.report_file):
                with open(self.args.report_file, 'r', newline='') as file_contents:
                    if self.args.report_file.endswith('.json'):
                        try:
                            self.report = json.load(file_contents)
                        except json_exception_class:
                            print(_(messages.REPORT_VALIDATE_INVALID_JSON % self.args.report_file))
                            sys.exit(1)
                    else:
                        # else we have a CSV file so read the contents
                        self.report = file_contents.read()
            else:
                print(_(messages.FILE_NOT_FOUND % self.args.report_file))
                sys.exit(1)

    def _build_data(self):
        """Construct the payload for a validating a report."""
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
        error = json_data.get('detail')
        print(_(messages.REPORT_VALIDATE_ERROR % error))
