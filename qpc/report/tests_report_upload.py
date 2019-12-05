#
# Copyright (c) 2018-2019 Red Hat, Inc.
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
from qpc.report import REPORT_UPLOAD_URI
from qpc.report.upload import ReportUploadCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests_mock

TMP_DETAILSFILE1 = ('/tmp/testdetailsreport1.json',
                    '{"id": 1,"sources":[{"facts": ["AB"],"server_id": "8"}]}')
TMP_DETAILSFILE2 = ('/tmp/testdetailsreport2.json',
                    '{"id": 2, \n "sources": [{"source_name": "source2"}]}')
TMP_NOTJSONFILE = ('/tmp/testnotjson.txt',
                   'not a json file')
TMP_BADDETAILS1 = ('/tmp/testbaddetailsreport_source.json',
                   '{"id": 4,"bsources":[{"facts": ["A"],"server_id": "8"}]}')
TMP_BADDETAILS2 = ('/tmp/testbadetailsreport_facts.json',
                   '{"id": 4,"sources":[{"bfacts": ["A"],"server_id": "8"}]}')
TMP_BADDETAILS3 = ('/tmp/testbaddetailsreport_server_id.json',
                   '{"id": 4,"sources":[{"facts": ["A"],"bserver_id": "8"}]}')
TMP_BADDETAILS4 = ('/tmp/testbaddetailsreport_bad_json.json',
                   '{"id":3,"sources"[this is bad]')
TMP_BADDETAILS5 = ('/tmp/testbaddetailsinvalidreporttype.json',
                   '{"report_type": "durham"}')
TMP_GOODDETAILS = ('/tmp/testgooddetailsreport.json',
                   '{"id": 4,"sources":[{"facts": ["A"],"server_id": "8"}]}')
NONEXIST_FILE = ('/tmp/does/not/exist/bad.json')
JSON_FILES_LIST = [TMP_DETAILSFILE1, TMP_DETAILSFILE2, TMP_NOTJSONFILE,
                   TMP_BADDETAILS1, TMP_BADDETAILS2, TMP_BADDETAILS3,
                   TMP_GOODDETAILS, TMP_BADDETAILS5]
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ReportUploadTests(unittest.TestCase):
    """Class for testing the scan show commands for qpc."""

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

    def test_upload_good_details_report(self):
        """Test uploading a good details report."""
        report_out = StringIO()

        put_report_data = {'report_id': 1}
        put_merge_url = get_server_location() + REPORT_UPLOAD_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(put_merge_url, status_code=201,
                        json=put_report_data)
            nac = ReportUploadCommand(SUBPARSER)
            args = Namespace(json_file=TMP_GOODDETAILS[0])
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertIn(messages.REPORT_SUCCESSFULLY_UPLOADED % ('1'),
                              report_out.getvalue().strip())

    def test_upload_bad_details_report(self):
        """Test uploading a bad details report."""
        report_out = StringIO()

        put_report_data = {'report_id': 1}
        put_merge_url = get_server_location() + REPORT_UPLOAD_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(put_merge_url, status_code=201,
                        json=put_report_data)
            nac = ReportUploadCommand(SUBPARSER)
            args = Namespace(json_file=TMP_BADDETAILS1[0])
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn(messages.REPORT_UPLOAD_FILE_INVALID_JSON % (TMP_BADDETAILS1[0]),
                          report_out.getvalue().strip())

    def test_upload_bad_details_report_no_fingerprints(self):
        """Test uploading a details report that produces no fingerprints."""
        report_out = StringIO()

        put_report_data = {
            'error': 'FAILED to create report id=23 - produced no valid fingerprints'}
        put_merge_url = get_server_location() + REPORT_UPLOAD_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(put_merge_url, status_code=400,
                        json=put_report_data)
            nac = ReportUploadCommand(SUBPARSER)
            args = Namespace(json_file=TMP_GOODDETAILS[0])
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn(messages.REPORT_FAILED_TO_UPLOADED % (put_report_data.get('error')),
                          report_out.getvalue().strip())
