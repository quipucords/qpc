#!/usr/bin/env python
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
"""Upload is used to upload files through the insights client."""

from __future__ import print_function

import os
import subprocess
import sys
import time

import qpc.insights as insights
from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.insights.utils import (InsightsCommands,
                                check_insights_install,
                                check_insights_version,
                                check_successful_upload,
                                format_subprocess_stderr,
                                format_upload_success)
from qpc.request import GET, request
from qpc.translation import _
from qpc.utils import (extract_json_from_tar,
                       validate_write_file,
                       write_file)

# pylint:disable=no-member
from requests import codes

CANONICAL_FACTS = ['bios_uuid', 'etc_machine_id', 'insights_client_id',
                   'ip_addresses', 'mac_addresses',
                   'subscription_manager_id', 'vm_uuid']


def verify_report_fingerprints(fingerprints):
    """Verify that report fingerprints contain canonical facts.

    :param fingerprints: dictionary of fingerprints to verify
    returns: valid, invalid fingerprints
    """
    valid_fp = []
    invalid_fp = []
    for fingerprint in fingerprints:
        found_facts = False
        for fact in CANONICAL_FACTS:
            if fingerprint.get(fact):
                found_facts = True
                break
        if found_facts:
            valid_fp.append(fingerprint)
        else:
            invalid_fp.append(fingerprint)

    return valid_fp, invalid_fp


# pylint: disable=too-few-public-methods
class InsightsUploadCommand(CliCommand):
    """Defines the Insights command.

    This command is for uploading QPC reports throught the insights client.
    """

    SUBCOMMAND = insights.SUBCOMMAND
    ACTION = insights.UPLOAD

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            insights.REPORT_URI, [codes.ok])
        id_group = self.parser.add_mutually_exclusive_group(required=True)
        id_group.add_argument('--report', dest='report_id',
                              metavar='REPORT_ID',
                              help=_(messages.INSIGHTS_REPORT_ID_HELP))
        id_group.add_argument('--scan-job', dest='scan_job_id',
                              metavar='SCAN_JOB_ID',
                              help=_(messages.INSIGHTS_SCAN_JOB_ID_HELP))

        self.parser.add_argument('--no-gpg', dest='no_gpg', action='store_true',
                                 help=_(messages.INSIGHTS_NO_GPG_HELP))
        self.tmp_tar_name = '/tmp/insights_tmp_%s.tar.gz' % (
            time.strftime('%Y%m%d_%H%M%S'))
        self.insights_command = None
        self.report_id = None

    def _check_insights_install(self):
        connection_test_command = self.insights_command.test_connection()
        process = subprocess.Popen(connection_test_command,
                                   stderr=subprocess.PIPE)
        streamdata = format_subprocess_stderr(process)
        code = process.returncode
        install_check = check_insights_install(streamdata)
        if not install_check or code != 0:
            print(_(messages.BAD_INSIGHTS_INSTALL %
                    (' '.join(connection_test_command))))
            sys.exit(1)

    def _check_insights_version(self):
        version_command = self.insights_command.version()
        process = subprocess.Popen(version_command,
                                   stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
        streamdata = format_subprocess_stderr(process)
        code = process.returncode
        version_check = check_insights_version(streamdata,
                                               insights.CLIENT_VERSION,
                                               insights.CORE_VERSION)
        if not version_check['results'] or code != 0:
            if 'client' in version_check.keys():
                print(_(messages.BAD_CLIENT_VERSION %
                        (version_check['client'],
                         insights.CLIENT_VERSION)))
            if 'core' in version_check.keys():
                print(_(messages.BAD_CORE_VERSION %
                        (version_check['core'],
                         insights.CORE_VERSION)))
            if 'error' in version_check.keys():
                print(_(messages.ERROR_INSIGHTS_VERSION %
                        (version_check['error'])))
            print(_(messages.CHECK_VERSION %
                    (' '.join(version_command))))
            sys.exit(1)

    def _validate_args(self):
        print(_(messages.INSIGHTS_REQUIRE_SUDO))
        CliCommand._validate_args(self)
        print_scan_job_message = False
        self.req_headers = {'Accept': 'application/json+gzip'}
        if self.args.report_id is None:
            response = request(parser=self.parser, method=GET,
                               path='%s%s' % (scan.SCAN_JOB_URI,
                                              self.args.scan_job_id),
                               payload=None)
            if response.status_code == codes.ok:  # pylint: disable=no-member
                json_data = response.json()
                self.report_id = json_data.get('report_id')
                if self.report_id is None:
                    print(_(messages.REPORT_NO_DEPLOYMENTS_REPORT_FOR_SJ %
                            self.args.scan_job_id))
                    sys.exit(1)
            else:
                print(_(messages.REPORT_SJ_DOES_NOT_EXIST %
                        self.args.scan_job_id))
                sys.exit(1)
            print_scan_job_message = True
        else:
            self.report_id = self.args.report_id
        if self.args.no_gpg:
            self.insights_command = InsightsCommands(no_gpg=True)
        else:
            self.insights_command = InsightsCommands()
        self._check_insights_install()
        self._check_insights_version()
        print(_(messages.INSIGHTS_IS_VERIFIED))
        try:
            validate_write_file(self.tmp_tar_name, 'tmp_tar_name')
        except ValueError:
            print(_(messages.INSIGHTS_TMP_ERROR % self.tmp_tar_name))
            sys.exit(1)
        if print_scan_job_message:
            print(_(messages.INSIGHTS_SCAN_JOB_ID_PRODUCED %
                    (self.args.scan_job_id,
                     self.report_id)))
        print(_(messages.INSIGHTS_RETRIEVE_REPORT % self.report_id))

    def verify_report_details(self):
        """
        Verify that the report contents are a valid deployments report.

        :returns boolean regarding report validity, error (str) if error occurred
        """
        # pylint: disable=too-many-locals
        error = None
        deployments_report = extract_json_from_tar(self.response.content,
                                                   print_pretty=False)
        # validate required keys
        required_keys = ['report_platform_id',
                         'report_id',
                         'report_version',
                         'report_type',
                         'system_fingerprints']
        missing_keys = []
        for key in required_keys:
            required_key = deployments_report.get(key)
            if not required_key:
                missing_keys.append(key)

        if missing_keys:
            missing_keys_str = ', '.join(missing_keys)
            error = messages.INSIGHTS_REPORT_MISSING_FIELDS % missing_keys_str
            return False, error

        # validate report type
        report_id = deployments_report.get('report_id')
        if deployments_report['report_type'] != 'deployments':
            error = messages.INSIGHTS_INVALID_REPORT_TYPE % deployments_report['report_type']
            return False, error

        # validate fingerprints contain canonical facts
        fingerprints = deployments_report.get('system_fingerprints')
        valid_fp, invalid_fp = verify_report_fingerprints(fingerprints)
        print(_(messages.INSIGHTS_TOTAL_VALID_FP % (report_id,
                                                    (len(valid_fp)),
                                                    str(len(fingerprints)))))
        if invalid_fp:
            print(_(messages.INSIGHTS_TOTAL_INVALID_FP % (report_id,
                                                          ', '.join(CANONICAL_FACTS))))
            for fingerprint in invalid_fp:
                fp_name = fingerprint.get('name', 'UNKNOWN')
                fp_metadata = fingerprint.get('metadata', {})
                name_metadata = fp_metadata.get('name', {})
                source_name = name_metadata.get('source_name', 'UNKNOWN')

                print(_(messages.INSIGHTS_INVALID_FP_NAME % (source_name, fp_name)))
        if not valid_fp:
            error = messages.INSIGHTS_REPORT_NO_VALID_FP
            return False, error
        return True, error

    def _build_req_params(self):
        self.req_path = '%s%s%s' % (
            insights.REPORT_URI,
            str(self.report_id),
            insights.DEPLOYMENTS_PATH_SUFFIX)

    def _handle_response_success(self):
        valid, error = self.verify_report_details()
        if not valid:
            print(_(messages.INVALID_REPORT_INSIGHTS_UPLOAD % (self.report_id, error)))
            sys.exit(1)
        write_file(self.tmp_tar_name,
                   self.response.content,
                   True)
        upload_command = self.insights_command.upload(self.tmp_tar_name)
        process = subprocess.Popen(upload_command, stderr=subprocess.PIPE)
        streamdata = format_subprocess_stderr(process)
        code = process.returncode
        report_check = check_successful_upload(streamdata)
        print(_(messages.INSIGHTS_UPLOAD_REPORT % self.report_id))
        if not report_check or code != 0:
            print(_(messages.BAD_INSIGHTS_UPLOAD % (self.report_id, (' '.join(upload_command)))))
            os.remove(self.tmp_tar_name)
            sys.exit(1)
        else:
            format_streamdata = format_upload_success(streamdata)
            print(_(format_streamdata))
            os.remove(self.tmp_tar_name)

    def _handle_response_error(self):
        print(_(messages.INSIGHTS_REPORT_NOT_FOUND % (self.args.report_id)))
        sys.exit(1)
