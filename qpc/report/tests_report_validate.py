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
"""Test the CLI module."""

import os
import sys
import time
import unittest
from argparse import ArgumentParser, Namespace
from io import StringIO

from qpc import messages
from qpc.report import VALIDATE_URI
from qpc.report.validate import ReportValidateCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests_mock

TMP_DETAILSFILE1 = ('/tmp/testdetailsreport1.json',
                    '{"id": 1,"sources":[{"facts": ["AB"],"server_id": "8"}]}')
TMP_NOTJSONFILE = ('/tmp/testnotjson.csv',
                   '\n\rnot a json file')
TMP_INVALID_JSON = ('/tmp/invalid.json',
                    '{"id": Not valid json.')
NONEXIST_FILE = ('/tmp/does/not/exist/bad.json')
JSON_FILES_LIST = [TMP_DETAILSFILE1, TMP_NOTJSONFILE,
                   TMP_INVALID_JSON]
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ReportValidateTests(unittest.TestCase):
    """Class for testing the report validate commands for qpc."""

    # pylint: disable=invalid-name
    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        self.test_json_filename = 'test_%d.json' % time.time()
        self.test_csv_filename = 'test_%d.csv' % time.time()
        sys.stderr = HushUpStderr()
        for file in JSON_FILES_LIST:
            if os.path.isfile(file[0]):
                os.remove(file[0])
            with open(file[0], 'w') as test_file:
                test_file.write(file[1])

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        for file in JSON_FILES_LIST:
            if os.path.isfile(file[0]):
                os.remove(file[0])
        sys.stderr = self.orig_stderr
        try:
            os.remove(self.test_json_filename)
        except FileNotFoundError:
            pass
        try:
            os.remove(self.test_csv_filename)
        except FileNotFoundError:
            pass

    def test_successful_report_validate_json(self):
        """Testing report validate command with report file and hash."""
        report_out = StringIO()

        put_report_data = {'detail': True}
        put_merge_url = get_server_location() + VALIDATE_URI
        with requests_mock.Mocker() as mocker:
            mocker.put(put_merge_url, status_code=200,
                       json=put_report_data)
            rvc = ReportValidateCommand(SUBPARSER)
            args = Namespace(report_file=TMP_DETAILSFILE1[0],
                             report_hash='fooo')
            with redirect_stdout(report_out):
                rvc.main(args)
                self.assertEqual(messages.REPORT_VALID % TMP_DETAILSFILE1[0],
                                 report_out.getvalue().strip())

    def test_successful_report_validate_csv(self):
        """Testing report validate command with report file and hash."""
        report_out = StringIO()

        put_report_data = {'detail': False}
        put_merge_url = get_server_location() + VALIDATE_URI
        with requests_mock.Mocker() as mocker:
            mocker.put(put_merge_url, status_code=200,
                       json=put_report_data)
            rvc = ReportValidateCommand(SUBPARSER)
            args = Namespace(report_file=TMP_NOTJSONFILE[0],
                             report_hash='fooo')
            with redirect_stdout(report_out):
                rvc.main(args)
                self.assertEqual(messages.REPORT_INVALID % TMP_NOTJSONFILE[0],
                                 report_out.getvalue().strip())

    def test_report_validate_fnf(self):
        """Testing report validate file not found."""
        report_out = StringIO()
        rvc = ReportValidateCommand(SUBPARSER)
        args = Namespace(report_file=NONEXIST_FILE[0],
                         report_hash='foo')
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                rvc.main(args)

    def test_report_validate_invalid_json(self):
        """Testing report validate invalid json."""
        report_out = StringIO()
        rvc = ReportValidateCommand(SUBPARSER)
        args = Namespace(report_file=TMP_INVALID_JSON[0],
                         report_hash='foo')
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                rvc.main(args)

    def test_error_report_validate_json(self):
        """Testing report validate command that results in an error."""
        report_out = StringIO()

        put_report_data = {'detail':
                           'A report and hash must be provided to validate.'}
        put_merge_url = get_server_location() + VALIDATE_URI
        with requests_mock.Mocker() as mocker:
            mocker.put(put_merge_url, status_code=424,
                       json=put_report_data)
            rvc = ReportValidateCommand(SUBPARSER)
            args = Namespace(report_file=TMP_DETAILSFILE1[0],
                             report_hash='fooo')
            with redirect_stdout(report_out):
                rvc.main(args)
                self.assertEqual(
                    messages.REPORT_VALIDATE_ERROR % put_report_data['detail'],
                    report_out.getvalue().strip())
