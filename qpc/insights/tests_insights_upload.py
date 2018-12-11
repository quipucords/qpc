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

import sys
import unittest
from unittest.mock import Mock, patch
from argparse import ArgumentParser, Namespace  # noqa: I100
from io import StringIO  # noqa: I100

from qpc import messages
from qpc.insights import REPORT_URI
from qpc.insights.upload import InsightsUploadCommand, verify_report_fingerprints
from qpc.scan import SCAN_JOB_URI
from qpc.tests_utilities import (DEFAULT_CONFIG, HushUpStderr,
                                 create_tar_buffer, redirect_stdout)
from qpc.utils import get_server_location, write_server_config

import requests_mock

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class InsightsUploadCliTests(unittest.TestCase):
    """Class for testing the scan job commands for qpc."""

    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        self.orig_stderr = sys.stderr
        self.success_json = {
            'report_id': 1,
            'report_type': 'deployments',
            'report_version': '1.0.0.1b025b8',
            'status': 'completed',
            'report_platform_id': '5f2cc1fd-ec66-4c67-be1b-171a595ce319',
            'system_fingerprints': [{'bios_uuid': 'value'}]}
        self.json_missing_fingerprints = {
            'report_id': 1,
            'report_type': 'deployments',
            'report_version': '1.0.0.1b025b8',
            'status': 'completed',
            'report_platform_id': '5f2cc1fd-ec66-4c67-be1b-171a595ce319',
            'system_fingerprints': []}

        sys.stderr = HushUpStderr()
        # pylint:disable=line-too-long
        self.success_effect = [(None, b'Running Connection Tests...\nConnection test config:\n=== Begin Certificate Chain Test ===\ndepth=1\nverify error:num=0\nverify return:1\ndepth=0\nverify error:num=0\nverify return:1\n=== End Certificate Chain Test: SUCCESS ===\n\n=== Begin Upload URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: \nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/uploads/\n=== End Upload URL Connection Test: SUCCESS ===\n\n=== Begin API URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: lub-dub\nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/\n=== End API URL Connection Test: SUCCESS ===\n\n\nConnectivity tests completed successfully\nSee /var/log/insights-client/insights-client.log for more details.\n'), (b'Client: 3.0.3-2\nCore: 3.0.8-1\n', b''), (None, b'Uploading Insights data.\nSuccessfully uploaded report for.\n')]  # noqa: E501

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_valid_report(self, subprocess):
        """Testing response with a vaild report id."""
        subprocess.return_value.communicate.side_effect = self.success_effect
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        buffer_content = create_tar_buffer([self.success_json])
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200,
                       content=buffer_content)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job=None,
                             dev=None)
            with redirect_stdout(report_out):
                with patch('qpc.insights.upload.extract_json_from_tar',
                           return_value=self.success_json):
                    nac.main(args)
                    self.assertIn('Successfully uploaded report',
                                  report_out.getvalue().strip())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_invalid_report(self, subprocess):
        """Testing response with an invaild report id."""
        subprocess.return_value.communicate.side_effect = self.success_effect
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + REPORT_URI + '1/deployments/'
        buffer_content = create_tar_buffer([self.json_missing_fingerprints])
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200,
                       content=buffer_content)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job=None,
                             dev=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    with patch('qpc.insights.upload.extract_json_from_tar',
                               return_value=self.json_missing_fingerprints):
                        nac.main(args)
                        self.assertIn(
                            'Report "%s" contained no valid fingerprints.'
                            % self.json_missing_fingerprints.get('report_id'),
                            report_out.getvalue().strip())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_valid_scan_job(self, subprocess):
        """Testing response with a valid scan job id."""
        subprocess.return_value.communicate.side_effect = self.success_effect
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_scanjob_url = get_server_location() + \
            SCAN_JOB_URI + '1'
        get_scanjob_json_data = {'id': 1, 'report_id': 1}
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        get_report_json_data = {'id': 1, 'report': [{'key': 'value'}]}
        buffer_content = create_tar_buffer([get_report_json_data])
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200,
                       json=get_scanjob_json_data)
            mocker.get(get_report_url, status_code=200,
                       content=buffer_content)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(scan_job_id='1',
                             report_id=None,
                             dev=None)
            with redirect_stdout(report_out):
                with patch('qpc.insights.upload.InsightsUploadCommand.verify_report_details',
                           return_value=True):
                    nac.main(args)
                    self.assertIn('Successfully uploaded report',
                                  report_out.getvalue().strip())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_nonexistent_report(self, subprocess):
        """Testing error response with an invalid report id."""
        subprocess.return_value.communicate.side_effect = self.success_effect
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=404, content=None)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job_id=None,
                             dev=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn(messages.INSIGHTS_REPORT_NOT_FOUND %
                          ('1'), report_out.getvalue().strip())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_unexpected_response_install(self, subprocess):
        """Testing error response with unexpected response install."""
        subprocess.return_value.communicate.return_value =\
            (None, b'Unknown Response')
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=400, json=None)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job_id=None,
                             dev=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn(messages.BAD_INSIGHTS_INSTALL %
                          ('sudo insights-client --test-connection'),
                          report_out.getvalue())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_unexpected_response_version(self, subprocess):
        """Testing error response with unexpected response version."""
        # pylint:disable=line-too-long
        subprocess.return_value.communicate.side_effect = [(None, b'Running Connection Tests...\nConnection test config:\n=== Begin Certificate Chain Test ===\ndepth=1\nverify error:num=0\nverify return:1\ndepth=0\nverify error:num=0\nverify return:1\n=== End Certificate Chain Test: SUCCESS ===\n\n=== Begin Upload URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: \nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/uploads/\n=== End Upload URL Connection Test: SUCCESS ===\n\n=== Begin API URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: lub-dub\nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/\n=== End API URL Connection Test: SUCCESS ===\n\n\nConnectivity tests completed successfully\nSee /var/log/insights-client/insights-client.log for more details.\n'), (None, b'Unknown Response')]  # noqa: E501
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=400, json=None)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job_id=None,
                             dev=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn(messages.ERROR_INSIGHTS_VERSION.replace('%s', ''),
                          report_out.getvalue())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_unexpected_response_upload(self, subprocess):
        """Testing error response with unexpected upload."""
        # pylint:disable=line-too-long
        subprocess.return_value.communicate.side_effect = [(None, b'Running Connection Tests...\nConnection test config:\n=== Begin Certificate Chain Test ===\ndepth=1\nverify error:num=0\nverify return:1\ndepth=0\nverify error:num=0\nverify return:1\n=== End Certificate Chain Test: SUCCESS ===\n\n=== Begin Upload URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: \nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/uploads/\n=== End Upload URL Connection Test: SUCCESS ===\n\n=== Begin API URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: lub-dub\nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/\n=== End API URL Connection Test: SUCCESS ===\n\n\nConnectivity tests completed successfully\nSee /var/log/insights-client/insights-client.log for more details.\n'), (b'Client: 3.0.3-2\nCore: 3.0.8-1\n', b''), (None, b'Unknown Response')]  # noqa: E501
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/deployments/'
        get_report_json_data = {'id': 1, 'report': [{'key': 'value'}]}
        buffer_content = create_tar_buffer([get_report_json_data])
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200, content=buffer_content)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job_id=None,
                             dev=None)
            with self.assertRaises(SystemExit):
                with patch('qpc.insights.upload.InsightsUploadCommand.verify_report_details',
                           return_value=True):
                    nac.main(args)
                    self.assertIn(messages.BAD_INSIGHTS_UPLOAD.replace('%s', ''),
                                  report_out.getvalue())

    def test_verify_report_success(self):
        """Test to verify a QPC report with the correct structure passes validation."""
        response = Mock(content=self.success_json)
        command = InsightsUploadCommand(SUBPARSER)
        command.response = response
        with patch('qpc.insights.upload.extract_json_from_tar', return_value=self.success_json):
            status = InsightsUploadCommand.verify_report_details(command)
            self.assertEqual(status, True)

    def test_verify_report_missing_id(self):
        """Test to verify a QPC report with a missing id is failed."""
        report_json = {
            'report_type': 'deployments',
            'report_version': '1.0.0.1b025b8',
            'status': 'completed',
            'report_platform_id': '5f2cc1fd-ec66-4c67-be1b-171a595ce319',
            'system_fingerprints': [{'key': 'value'}]}

        response = Mock(content=report_json)
        command = InsightsUploadCommand(SUBPARSER)
        command.response = response
        with patch('qpc.insights.upload.extract_json_from_tar', return_value=report_json):
            status = InsightsUploadCommand.verify_report_details(command)
            self.assertEqual(status, False)

    def test_verify_report_fails_no_canonical_facts(self):
        """Test to verify a QPC report with the correct structure passes validation."""
        report_json = {
            'report_id': 1,
            'report_type': 'deployments',
            'report_version': '1.0.0.1b025b8',
            'status': 'completed',
            'report_platform_id': '5f2cc1fd-ec66-4c67-be1b-171a595ce319',
            'system_fingerprints': [{'name': 'value'}]}
        response = Mock(content=report_json)
        command = InsightsUploadCommand(SUBPARSER)
        command.response = response
        with patch('qpc.insights.upload.extract_json_from_tar', return_value=report_json):
            status = InsightsUploadCommand.verify_report_details(command)
            self.assertEqual(status, False)

    def test_verify_report_invalid_report_type(self):
        """Test to verify a QPC report with an invalid report_type is failed."""
        report_json = {
            'report_id': 1,
            'report_type': 'details',
            'report_version': '1.0.0.1b025b8',
            'status': 'completed',
            'report_platform_id': '5f2cc1fd-ec66-4c67-be1b-171a595ce319',
            'system_fingerprints': [{'key': 'value'}]}

        response = Mock(content=report_json)
        command = InsightsUploadCommand(SUBPARSER)
        command.response = response
        with patch('qpc.insights.upload.extract_json_from_tar', return_value=report_json):
            status = InsightsUploadCommand.verify_report_details(command)
            self.assertEqual(status, False)

    def test_verify_report_missing_version(self):
        """Test to verify a QPC report missing report_version is failed."""
        report_json = {
            'report_id': 1,
            'report_type': 'deployments',
            'status': 'completed',
            'report_platform_id': '5f2cc1fd-ec66-4c67-be1b-171a595ce319',
            'system_fingerprints': [{'key': 'value'}]}

        response = Mock(content=report_json)
        command = InsightsUploadCommand(SUBPARSER)
        command.response = response
        with patch('qpc.insights.upload.extract_json_from_tar', return_value=report_json):
            status = InsightsUploadCommand.verify_report_details(command)
            self.assertEqual(status, False)

    def test_verify_report_missing_platform_id(self):
        """Test to verify a QPC report missing report_platform_id is failed."""
        report_json = {
            'report_id': 1,
            'report_type': 'deployments',
            'report_version': '1.0.0.1b025b8',
            'status': 'completed',
            'system_fingerprints': [{'key': 'value'}]}

        response = Mock(content=report_json)
        command = InsightsUploadCommand(SUBPARSER)
        command.response = response
        with patch('qpc.insights.upload.extract_json_from_tar', return_value=report_json):
            status = InsightsUploadCommand.verify_report_details(command)
            self.assertEqual(status, False)

    def test_verify_report_missing_fingerprints(self):
        """Test to verify a QPC report with empty fingerprints is failed."""
        response = Mock(content=self.json_missing_fingerprints)
        command = InsightsUploadCommand(SUBPARSER)
        command.response = response
        with patch('qpc.insights.upload.extract_json_from_tar',
                   return_value=self.json_missing_fingerprints):
            status = InsightsUploadCommand.verify_report_details(command)
            self.assertEqual(status, False)

    def test_verify_report_fingerprints(self):
        """Test fingerprint verification."""
        # test all valid fingerprints
        fingerprints = [{'bios_uuid': 'value', 'name': 'value'},
                        {'insights_client_id': 'value', 'name': 'foo'},
                        {'ip_addresses': 'value', 'name': 'foo'},
                        {'mac_addresses': 'value', 'name': 'foo'},
                        {'vm_uuid': 'value', 'name': 'foo'},
                        {'etc_machine_id': 'value'},
                        {'subscription_manager_id': 'value'}]
        report_id = '1'
        valid = verify_report_fingerprints(fingerprints, report_id)

        self.assertEqual(valid, True)

        # test that mixed valid/invalid prints work as expected
        invalid_print = {'no': 'canonical facts',
                         'metadata': {'key': 'val',
                                      'name': {'source_name': 'NSource1'}}}
        fingerprints.append(invalid_print)
        valid = verify_report_fingerprints(fingerprints, report_id)
        self.assertEqual(valid, True)

        # test that if there are no valid fingerprints we return []
        fingerprints = [invalid_print]
        valid = verify_report_fingerprints(fingerprints, report_id)
        self.assertEqual(valid, False)
