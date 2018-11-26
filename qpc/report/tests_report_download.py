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
"""Test the CLI module."""


import os
import sys
import time
import unittest
from argparse import ArgumentParser, Namespace
from io import StringIO

from qpc import messages
from qpc.cli import CLI
from qpc.report import REPORT_URI
from qpc.report.download import ReportDownloadCommand
from qpc.scan import SCAN_JOB_URI
from qpc.tests_utilities import (DEFAULT_CONFIG, HushUpStderr,
                                 create_tar_buffer, redirect_stdout)
from qpc.utils import get_server_location, write_server_config

import requests_mock

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ReportDetailsTests(unittest.TestCase):
    """Class for testing the report download command."""

    # pylint: disable=invalid-name
    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        self.test_tar_filename = 'test_%d.tar.gz' % time.time()
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr
        try:
            os.remove(self.test_tar_filename)
        except FileNotFoundError:
            pass

    def test_download_scan_job(self):
        """Testing download with scan job id."""
        report_out = StringIO()
        get_scanjob_url = get_server_location()
        get_scanjob_url = get_server_location() + \
            SCAN_JOB_URI + '1'
        get_scanjob_json_data = {'id': 1, 'report_id': 1}
        get_report_url = get_server_location() + \
            REPORT_URI + '1'
        get_report_json_data = {'id': 1, 'report': [{'key': 'value'}]}
        test_dict = dict()
        test_dict['test.json'] = get_report_json_data
        buffer_content = create_tar_buffer(test_dict)

        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200,
                       json=get_scanjob_json_data)
            mocker.get(get_report_url, status_code=200,
                       content=buffer_content)
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(scan_job_id='1',
                             report_id=None,
                             output_json=True,
                             output_csv=False,
                             path=self.test_tar_filename)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.REPORT_SUCCESSFULLY_WRITTEN)

    def test_download_report_id(self):
        """Testing download with report id."""
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1'
        get_report_json_data = {'id': 1, 'report': [{'key': 'value'}]}
        test_dict = dict()
        test_dict[self.test_tar_filename] = get_report_json_data
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200,
                       content=buffer_content)
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(scan_job_id=None,
                             report_id='1',
                             output_json=True,
                             output_csv=False,
                             path=self.test_tar_filename)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.REPORT_SUCCESSFULLY_WRITTEN)

    def test_download_output_directory(self):
        """Testing fail because of output directory."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'report', 'download',
                        '--output-file', '/foo/bar']
            CLI().main()

    def test_download_output_directory_not_exist(self):
        """Testing fail because output directory does not exist."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'report', 'download',
                        '--output-file', '/foo/bar/']
            CLI().main()

    def test_download_output_file_empty(self):
        """Testing fail because output file empty."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'report', 'download',
                        '--json', '--output-file', '']
            CLI().main()

    def test_download_report_empty(self):
        """Testing fail because output file empty."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'report', 'download',
                        '--report', '', '--output-file', 'test.json']
            CLI().main()

    def test_download_scan_job_not_exist(self):
        """Summary report with nonexistent scanjob."""
        report_out = StringIO()
        get_scanjob_url = get_server_location() + \
            SCAN_JOB_URI + '1'
        get_scanjob_json_data = {'id': 1, 'report_id': 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=400,
                       json=get_scanjob_json_data)
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(scan_job_id='1',
                             output_json=True,
                             report_id=None,
                             output_csv=False,
                             path=self.test_tar_filename)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
                    self.assertEqual(report_out.getvalue(),
                                     messages.REPORT_SJ_DOES_NOT_EXIST)

    def test_summary_report_invalid_scan_job(self):
        """Summary report with scanjob but no report_id."""
        report_out = StringIO()

        get_scanjob_url = get_server_location() + \
            SCAN_JOB_URI + '1'
        get_scanjob_json_data = {'id': 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200,
                       json=get_scanjob_json_data)
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(scan_job_id='1',
                             report_id=None,
                             output_json=True,
                             output_csv=False,
                             path=self.test_tar_filename)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
                    self.assertEqual(
                        report_out.getvalue(),
                        messages.REPORT_NO_DEPLOYMENTS_REPORT_FOR_SJ)
