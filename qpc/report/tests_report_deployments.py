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

import json
import os
import sys
import time
import unittest
from unittest.mock import patch
from argparse import ArgumentParser, Namespace  # noqa: I100
from io import StringIO  # noqa: I100

from qpc import messages
from qpc.cli import CLI
from qpc.report import REPORT_URI
from qpc.report.deployments import ReportDeploymentsCommand
from qpc.scan import SCAN_JOB_URI
from qpc.tests_utilities import (DEFAULT_CONFIG, HushUpStderr,
                                 redirect_stdout)
from qpc.utils import create_tar_buffer, get_server_location, write_server_config

import requests_mock

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ReportDeploymentsTests(unittest.TestCase):
    """Class for testing the deployments report command."""

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

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr
        try:
            os.remove(self.test_json_filename)
        except FileNotFoundError:
            pass
        try:
            os.remove(self.test_csv_filename)
        except FileNotFoundError:
            pass

    def test_deployments_report_as_json(self):
        """Testing retreiving deployments report as json."""
        report_out = StringIO()

        get_scanjob_url = get_server_location() + \
            SCAN_JOB_URI + '1'
        get_scanjob_json_data = {'id': 1, 'report_id': 1}
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        get_report_json_data = {'id': 1, 'report': [{'key': 'value'}]}
        test_dict = dict()
        test_dict[self.test_json_filename] = get_report_json_data
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200,
                       json=get_scanjob_json_data)
            mocker.get(get_report_url, status_code=200,
                       content=buffer_content)
            nac = ReportDeploymentsCommand(SUBPARSER)
            args = Namespace(scan_job_id='1',
                             report_id=None,
                             output_json=True,
                             output_csv=False,
                             path=self.test_json_filename)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.REPORT_SUCCESSFULLY_WRITTEN)
                with open(self.test_json_filename, 'r') as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                self.assertDictEqual(get_report_json_data, file_content_dict)

    def test_deployments_report_as_json_report_id(self):
        """Testing retreiving deployments report as json with report id."""
        report_out = StringIO()

        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        get_report_json_data = {'id': 1, 'report': [{'key': 'value'}]}
        test_dict = dict()
        test_dict[self.test_json_filename] = get_report_json_data
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200,
                       content=buffer_content)
            nac = ReportDeploymentsCommand(SUBPARSER)
            args = Namespace(scan_job_id=None,
                             report_id='1',
                             output_json=True,
                             output_csv=False,
                             path=self.test_json_filename)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.REPORT_SUCCESSFULLY_WRITTEN)
                with open(self.test_json_filename, 'r') as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                self.assertDictEqual(get_report_json_data, file_content_dict)

    def test_deployments_report_as_csv(self):
        """Testing retreiving deployments report as csv."""
        report_out = StringIO()
        get_scanjob_url = get_server_location() + \
            SCAN_JOB_URI + '1'
        get_scanjob_json_data = {'id': 1, 'report_id': 1}
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        get_report_csv_data = 'Report\n'
        get_report_csv_data += '1\n\n\n'
        get_report_csv_data += 'key\n'
        get_report_csv_data += 'value\n'

        get_report_csv_data = {'id': 1, 'report': [{'key': 'value'}]}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200,
                       json=get_scanjob_json_data)
            mocker.get(get_report_url, status_code=200,
                       json=get_report_csv_data)
            nac = ReportDeploymentsCommand(SUBPARSER)
            args = Namespace(scan_job_id='1',
                             report_id=None,
                             output_json=False,
                             output_csv=True,
                             path=self.test_csv_filename)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.REPORT_SUCCESSFULLY_WRITTEN)
                with open(self.test_csv_filename, 'r') as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                self.assertDictEqual(get_report_csv_data, file_content_dict)

    # Test validation
    def test_deployments_report_output_directory(self):
        """Testing fail because output directory."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'report', 'deployments',
                        '--json', '--output-file', '/']
            CLI().main()

    def test_deployments_report_output_directory_not_exist(self):
        """Testing fail because output directory does not exist."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'report', 'deployments',
                        '--json', '--output-file', '/foo/bar/']
            CLI().main()

    def test_deployments_report_output_file_empty(self):
        """Testing fail because output file empty."""
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/qpc', 'report', 'deployments',
                        '--json', '--output-file', '']
            CLI().main()

    def test_deployments_report_scan_job_not_exist(self):
        """Deployments report with nonexistent scanjob."""
        report_out = StringIO()

        get_scanjob_url = get_server_location() + \
            SCAN_JOB_URI + '1'
        get_scanjob_json_data = {'id': 1, 'report_id': 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=400,
                       json=get_scanjob_json_data)
            nac = ReportDeploymentsCommand(SUBPARSER)
            args = Namespace(scan_job_id='1',
                             output_json=True,
                             report_id=None,
                             output_csv=False,
                             path=self.test_json_filename)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
                    self.assertEqual(report_out.getvalue(),
                                     messages.REPORT_SJ_DOES_NOT_EXIST)

    def test_deployments_report_invalid_scan_job(self):
        """Deployments report with scanjob but no report_id."""
        report_out = StringIO()

        get_scanjob_url = get_server_location() + \
            SCAN_JOB_URI + '1'
        get_scanjob_json_data = {'id': 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200,
                       json=get_scanjob_json_data)
            nac = ReportDeploymentsCommand(SUBPARSER)
            args = Namespace(scan_job_id='1',
                             report_id=None,
                             output_json=True,
                             output_csv=False,
                             path=self.test_json_filename)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
                    self.assertEqual(
                        report_out.getvalue(),
                        messages.REPORT_NO_DEPLOYMENTS_REPORT_FOR_SJ)

    @patch('qpc.report.deployments.write_file')
    def test_deployments_file_fails_to_write(self, file):
        """Testing deployments failure while writing to file."""
        file.side_effect = EnvironmentError()
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        get_report_json_data = {'id': 1, 'report': [{'key': 'value'}]}
        test_dict = dict()
        test_dict[self.test_json_filename] = get_report_json_data
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200,
                       content=buffer_content)
            nac = ReportDeploymentsCommand(SUBPARSER)
            args = Namespace(scan_job_id=None,
                             report_id='1',
                             output_json=True,
                             output_csv=False,
                             path=self.test_json_filename)
            with redirect_stdout(report_out):
                with self.assertRaises(SystemExit):
                    nac.main(args)
                err_msg = (messages.WRITE_FILE_ERROR %
                           (self.test_json_filename, ''))
                self.assertEqual(report_out.getvalue().strip(), err_msg)

    def test_deployments_nonexistent_directory(self):
        """Testing error for nonexistent directory in output."""
        fake_dir = '/cody/is/awesome/'
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        get_report_json_data = {'id': 1, 'report': [{'key': 'value'}]}
        test_dict = dict()
        test_dict[self.test_json_filename] = get_report_json_data
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200,
                       content=buffer_content)
            nac = ReportDeploymentsCommand(SUBPARSER)
            args = Namespace(scan_job_id=None,
                             report_id='1',
                             output_json=True,
                             output_csv=False,
                             path=fake_dir)
            with redirect_stdout(report_out):
                with self.assertRaises(SystemExit):
                    nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 (messages.REPORT_DIRECTORY_DOES_NOT_EXIST %
                                  os.path.dirname(fake_dir)))

    def test_deployments_report_id_not_exist(self):
        """Test deployments with nonexistent report id."""
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        get_report_json_data = {'id': 1, 'report': [{'key': 'value'}]}
        test_dict = dict()
        test_dict[self.test_json_filename] = get_report_json_data
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=400,
                       content=buffer_content)
            nac = ReportDeploymentsCommand(SUBPARSER)
            args = Namespace(scan_job_id=None,
                             report_id='1',
                             output_json=True,
                             output_csv=False,
                             path=self.test_json_filename)
            with redirect_stdout(report_out):
                with self.assertRaises(SystemExit):
                    nac.main(args)
                err = (messages.REPORT_NO_DEPLOYMENTS_REPORT_FOR_REPORT_ID %
                       1)
                self.assertEqual(report_out.getvalue().strip(), err)

    def test_deployments_report_error_scan_job(self):
        """Testing error with scan job id."""
        report_out = StringIO()

        get_scanjob_url = get_server_location() + \
            SCAN_JOB_URI + '1'
        get_scanjob_json_data = {'id': 1, 'report_id': 1}
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        get_report_json_data = {'id': 1, 'report': [{'key': 'value'}]}
        test_dict = dict()
        test_dict[self.test_json_filename] = get_report_json_data
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200,
                       json=get_scanjob_json_data)
            mocker.get(get_report_url, status_code=400,
                       content=buffer_content)
            nac = ReportDeploymentsCommand(SUBPARSER)
            args = Namespace(scan_job_id='1',
                             report_id=None,
                             output_json=True,
                             output_csv=False,
                             path=self.test_json_filename)
            with redirect_stdout(report_out):
                with self.assertRaises(SystemExit):
                    nac.main(args)
                self.assertEqual(report_out.getvalue().strip(),
                                 messages.REPORT_NO_DEPLOYMENTS_REPORT_FOR_SJ %
                                 1)
