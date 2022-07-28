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

import json
import os
import sys
import time
import unittest
from unittest.mock import patch
from argparse import ArgumentParser, Namespace  # noqa: I100
from io import StringIO  # noqa: I100

from qpc import messages
from qpc.insights import CLIENT_VERSION, CORE_VERSION, REPORT_URI
from qpc.insights.upload import InsightsUploadCommand, verify_report_hosts
from qpc.release import VERSION
from qpc.scan import SCAN_JOB_URI
from qpc.tests_utilities import (DEFAULT_CONFIG, HushUpStderr, redirect_stdout)
from qpc.utils import (create_tar_buffer,
                       get_server_location,
                       write_file,
                       write_server_config)

import requests_mock

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


# pylint: disable=too-many-public-methods,protected-access
@unittest.skip(
    "Upload subcommand is temporarily disable to "
    "prevent user's confusion with the publish command."
)
class InsightsUploadCliTests(unittest.TestCase):
    """Class for testing the scan job commands for qpc."""

    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        self.orig_stderr = sys.stderr
        self.success_json = {
            'report_id': 1,
            'report_type': 'insights',
            'report_version': '0.9.0.1b025b8',
            'status': 'completed',
            'report_platform_id': '5f2cc1fd-ec66-4c67-be1b-171a595ce319',
            'hosts': {
                '2f2cc1fd-ec66-4c67-be1b-171a595ce319': {
                    'bios_uuid': 'value'}}}
        self.json_missing_hosts = {
            'report_id': 1,
            'report_type': 'insights',
            'report_version': '0.9.0.1b025b8',
            'status': 'completed',
            'report_platform_id': '5f2cc1fd-ec66-4c67-be1b-171a595ce319',
            'hosts': {}}

        sys.stderr = HushUpStderr()
        # pylint:disable=line-too-long
        self.success_effect = [(None, b'Running Connection Tests...\nConnection test config:\n=== Begin Certificate Chain Test ===\ndepth=1\nverify error:num=0\nverify return:1\ndepth=0\nverify error:num=0\nverify return:1\n=== End Certificate Chain Test: SUCCESS ===\n\n=== Begin Upload URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: \nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/uploads/\n=== End Upload URL Connection Test: SUCCESS ===\n\n=== Begin API URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: lub-dub\nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/\n=== End API URL Connection Test: SUCCESS ===\n\n\nConnectivity tests completed successfully\nSee /var/log/insights-client/insights-client.log for more details.\n'), (b'Client: 3.0.3-2\nCore: 3.0.72-1\n', b''), (None, b'Uploading Insights data.\nSuccessfully uploaded report for.\n')]  # noqa: E501

        self.tmp_tar_file = '/tmp/insights_tmp_%s.tar.gz' % (
            time.strftime('%Y%m%d_%H%M%S'))
        write_file(self.tmp_tar_file,
                   json.dumps(self.success_json),
                   False)
        self.dest_tar_file = '/tmp/insights_dest_%s.tar.gz' % (
            time.strftime('%Y%m%d_%H%M%S'))
        write_file(self.dest_tar_file,
                   json.dumps(self.success_json),
                   False)

        self.tmp_invalid_insights_json = '/tmp/insights_invalid_tmp_%s.json' % (
            time.strftime('%Y%m%d_%H%M%S'))
        write_file(self.tmp_invalid_insights_json,
                   json.dumps(self.json_missing_hosts),
                   False)

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr
        try:
            os.remove(self.tmp_tar_file)
        except FileNotFoundError:
            pass

        try:
            os.remove(self.tmp_invalid_insights_json)
        except FileNotFoundError:
            pass

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_valid_report(self, subprocess):
        """Testing response with a valid report id."""
        subprocess.return_value.communicate.side_effect = self.success_effect
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/insights/'
        buffer_content = create_tar_buffer({'insights.json': self.success_json})
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200,
                       headers={'X-Server-Version': VERSION},
                       content=buffer_content)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job=None,
                             input_file=None,
                             no_gpg=True)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertIn(messages.REPORT_INSIGHTS_REPORT_SUCCESSFULLY_UPLOADED,
                              report_out.getvalue().strip())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_bad_insights_upload(self, subprocess):
        """Testing response with a vaild report id."""
        # pylint:disable=line-too-long
        failed_effect = [
            (None, b''),
            (('Client: %s\nCore: %s\n' % (CLIENT_VERSION, CORE_VERSION)).encode(), b''),
            (None, b'failed to upload')]  # noqa: E501
        subprocess.return_value.communicate.side_effect = failed_effect
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/insights/'
        buffer_content = create_tar_buffer({'insights.json': self.success_json})
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200,
                       headers={'X-Server-Version': VERSION},
                       content=buffer_content)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job=None,
                             input_file=None,
                             no_gpg=True)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn((messages.BAD_INSIGHTS_UPLOAD % ('1', ''))[:10],
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
            REPORT_URI + '1/insights/'
        buffer_content = create_tar_buffer({'insights.json': self.success_json})
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200,
                       json=get_scanjob_json_data)
            mocker.get(get_report_url, status_code=200,
                       headers={'X-Server-Version': VERSION},
                       content=buffer_content)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(scan_job_id='1',
                             report_id=None,
                             input_file=None,
                             no_gpg=None)
            with redirect_stdout(report_out):
                nac.main(args)
                self.assertIn(messages.REPORT_INSIGHTS_REPORT_SUCCESSFULLY_UPLOADED,
                              report_out.getvalue().strip())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_valid_scan_job_no_report_id(self, subprocess):
        """Testing response with a valid scan job id but no report_id."""
        subprocess.return_value.communicate.side_effect = self.success_effect
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_scanjob_url = get_server_location() + \
            SCAN_JOB_URI + '1'
        get_scanjob_json_data = {'id': 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200,
                       json=get_scanjob_json_data)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(scan_job_id='1',
                             report_id=None,
                             input_file=None,
                             no_gpg=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn(messages.REPORT_NO_DEPLOYMENTS_REPORT_FOR_SJ % '1',
                          report_out.getvalue().strip())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_invalid_scan_job(self, subprocess):
        """Testing scan_job id not found."""
        subprocess.return_value.communicate.side_effect = self.success_effect
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_scanjob_url = get_server_location() + \
            SCAN_JOB_URI + '1'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=404,
                       json=None)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(scan_job_id='1',
                             report_id=None,
                             input_file=None,
                             no_gpg=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn(messages.REPORT_SJ_DOES_NOT_EXIST % '1',
                          report_out.getvalue().strip())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_nonexistent_report(self, subprocess):
        """Testing error response with an invalid report id."""
        subprocess.return_value.communicate.side_effect = self.success_effect
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/insights/'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=404,
                       headers={'X-Server-Version': VERSION},
                       content=None)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job_id=None,
                             input_file=None,
                             no_gpg=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn(messages.INSIGHTS_REPORT_NOT_FOUND %
                          ('1'), report_out.getvalue().strip())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_unexpected_response_version(self, subprocess):
        """Testing error response with unexpected response version."""
        # pylint:disable=line-too-long
        subprocess.return_value.communicate.side_effect = [(None, b'Running Connection Tests...\nConnection test config:\n=== Begin Certificate Chain Test ===\ndepth=1\nverify error:num=0\nverify return:1\ndepth=0\nverify error:num=0\nverify return:1\n=== End Certificate Chain Test: SUCCESS ===\n\n=== Begin Upload URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: \nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/uploads/\n=== End Upload URL Connection Test: SUCCESS ===\n\n=== Begin API URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: lub-dub\nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/\n=== End API URL Connection Test: SUCCESS ===\n\n\nConnectivity tests completed successfully\nSee /var/log/insights-client/insights-client.log for more details.\n'), (None, b'Unknown Response')]  # noqa: E501
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/insights/'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=400,
                       headers={'X-Server-Version': VERSION},
                       json=None)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job_id=None,
                             input_file=None,
                             no_gpg=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn(messages.ERROR_INSIGHTS_VERSION.replace('%s', ''),
                          report_out.getvalue())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_unexpected_response_upload(self, subprocess):
        """Testing error response with unexpected upload."""
        # pylint:disable=line-too-long
        subprocess.return_value.communicate.side_effect = [
            (None, b''),
            (('Client: %s\nCore: %s\n' % (CLIENT_VERSION, CORE_VERSION)).encode(), b''),
            (None, b'Unknown Response')
            ]  # noqa: E501
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/insights/'
        buffer_content = create_tar_buffer({'insights.json': self.success_json})
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200,
                       headers={'X-Server-Version': VERSION},
                       content=buffer_content)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job_id=None,
                             input_file=None,
                             no_gpg=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            self.assertIn((messages.BAD_INSIGHTS_UPLOAD % ('1', ''))[:10],
                          report_out.getvalue())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_outdated_version_response(self, subprocess):
        """Testing error response with unexpected response version."""
        # pylint:disable=line-too-long
        subprocess.return_value.communicate.side_effect = [(None, b'Running Connection Tests...\nConnection test config:\n=== Begin Certificate Chain Test ===\ndepth=1\nverify error:num=0\nverify return:1\ndepth=0\nverify error:num=0\nverify return:1\n=== End Certificate Chain Test: SUCCESS ===\n\n=== Begin Upload URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: \nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/uploads/\n=== End Upload URL Connection Test: SUCCESS ===\n\n=== Begin API URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: lub-dub\nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/\n=== End API URL Connection Test: SUCCESS ===\n\n\nConnectivity tests completed successfully\nSee /var/log/insights-client/insights-client.log for more details.\n'), (b'Client: 3.0.1\nCore: 3.0.8\n', b'')]  # noqa: E501
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/insights/'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=400,
                       headers={'X-Server-Version': VERSION},
                       json=None)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job_id=None,
                             input_file=None,
                             no_gpg=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            std_out = report_out.getvalue()
            cli_error_msg = (messages.BAD_CLIENT_VERSION %
                             ('3.0.1', CLIENT_VERSION))
            self.assertIn(cli_error_msg, std_out)
            cli_error_msg = (messages.BAD_CORE_VERSION %
                             ('3.0.8', CORE_VERSION))
            self.assertIn(cli_error_msg, std_out)

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_cmd_not_found_response(self, subprocess):
        """Testing error response with unexpected response version."""
        subprocess.return_value.communicate.side_effect = \
            [(None, b'insights-client: command not found')]
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        get_report_url = get_server_location() + \
            REPORT_URI + '1/insights/'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=400,
                       headers={'X-Server-Version': VERSION},
                       json=None)
            nac = InsightsUploadCommand(SUBPARSER)
            args = Namespace(report_id='1',
                             scan_job_id=None,
                             input_file=None,
                             no_gpg=None)
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
            cli_error_msg = (messages.BAD_INSIGHTS_INSTALL %
                             ('sudo insights-client --test-connection'))
            self.assertIn(cli_error_msg, report_out.getvalue())

    def test_verify_report_hosts(self):
        """Test fingerprint verification."""
        # test all valid fingerprints
        hosts = {'5f2cc1fd-ec66-4c67-be1b-171a595ce311': {'bios_uuid': 'value', 'name': 'value'},
                 '5f2cc1fd-ec66-4c67-be1b-171a595ce312': {
                     'insights_client_id': 'value', 'name': 'foo'},
                 '5f2cc1fd-ec66-4c67-be1b-171a595ce313': {'ip_addresses': 'value', 'name': 'foo'},
                 '5f2cc1fd-ec66-4c67-be1b-171a595ce314': {'mac_addresses': 'value', 'name': 'foo'},
                 '5f2cc1fd-ec66-4c67-be1b-171a595ce315': {'vm_uuid': 'value', 'name': 'foo'},
                 '5f2cc1fd-ec66-4c67-be1b-171a595ce316': {'etc_machine_id': 'value'},
                 '5f2cc1fd-ec66-4c67-be1b-171a595ce317': {'subscription_manager_id': 'value'}}
        valid, invalid = verify_report_hosts(hosts)

        self.assertEqual(valid, hosts)
        self.assertEqual(invalid, {})

        # test that mixed valid/invalid prints work as expected
        invalid_host = {'no': 'canonical facts',
                        'metadata': {'key': 'val',
                                     'name': {'source_name': 'NSource1'}}}
        invalid_host_id = '5f2cc1fd-ec66-4c67-be1b-171a595ce318'
        hosts['5f2cc1fd-ec66-4c67-be1b-171a595ce318'] = invalid_host
        valid, invalid = verify_report_hosts(hosts)
        hosts.pop(invalid_host_id, None)

        self.assertEqual(valid, hosts)
        self.assertEqual(invalid, {invalid_host_id: invalid_host})

        # test that if there are no valid hosts we return []
        hosts = {invalid_host_id: invalid_host}
        valid, invalid = verify_report_hosts(hosts)
        self.assertEqual(valid, {})
        self.assertEqual(invalid, hosts)

    def test_invalid_tmp_file(self):
        """Test invalid temp file (is dir)."""
        report_out = StringIO()
        command = InsightsUploadCommand(SUBPARSER)
        command.tmp_tar_name = '/'
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                command._validate_args()
        cli_error_msg = messages.INSIGHTS_TMP_ERROR % command.tmp_tar_name
        self.assertIn(cli_error_msg, report_out.getvalue())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_valid_report_from_file(self, subprocess):
        """Testing uploading insights report from local json file."""
        subprocess.return_value.communicate.side_effect = self.success_effect
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        nac = InsightsUploadCommand(SUBPARSER)
        args = Namespace(report_id=None,
                         scan_job=None,
                         input_file=self.dest_tar_file,
                         no_gpg=True)
        with redirect_stdout(report_out):
            nac.main(args)
            self.assertIn(messages.REPORT_INSIGHTS_REPORT_SUCCESSFULLY_UPLOADED,
                          report_out.getvalue().strip())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_invalid_local_tar_path(self, subprocess):
        """Testing uploading insights report with invalid path."""
        subprocess.return_value.communicate.side_effect = self.success_effect
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        nac = InsightsUploadCommand(SUBPARSER)
        args = Namespace(report_id=None,
                         scan_job=None,
                         input_file='your_face_is_a',
                         no_gpg=True)
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)
        self.assertIn(messages.INSIGHTS_LOCAL_REPORT_NOT % 'your_face_is_a',
                      report_out.getvalue().strip())

    @patch('qpc.insights.upload.subprocess.Popen')
    def test_insights_upload_not_tar_extension(self, subprocess):
        """Testing uploading insights report with invalid file extension."""
        random_file = '/tmp/insights_random_%s.txt' % (time.strftime('%Y%m%d_%H%M%S'))
        write_file(random_file, 'not really tar', False)

        subprocess.return_value.communicate.side_effect = self.success_effect
        subprocess.return_value.returncode = 0
        report_out = StringIO()
        nac = InsightsUploadCommand(SUBPARSER)
        args = Namespace(report_id=None,
                         scan_job=None,
                         input_file=random_file,
                         no_gpg=True)
        with self.assertRaises(SystemExit):
            with redirect_stdout(report_out):
                nac.main(args)
        self.assertIn(messages.INSIGHTS_LOCAL_REPORT_NOT_TAR_GZ % random_file,
                      report_out.getvalue().strip())
