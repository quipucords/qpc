#!/usr/bin/env python
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
"""Upload is used to upload files through the insights client."""

from __future__ import print_function

import os
import subprocess
import sys
import time
from argparse import SUPPRESS

import qpc.insights as insights
from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.insights.utils import (InsightsCommands,
                                check_insights_install,
                                check_insights_version,
                                check_successful_upload,
                                format_subprocess_stderr)
from qpc.request import GET, request
from qpc.translation import _
from qpc.utils import (validate_write_file,
                       write_file)

# pylint:disable=no-member
from requests import codes


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

        self.parser.add_argument('--dev', dest='dev', action='store_true',
                                 help=SUPPRESS)
        self.tmp_tar_name = '/tmp/insights_tmp_%s.tar.gz' % (
            time.strftime('%Y%m%d_%H%M%S'))
        self.insights_command = None
        self.report_id = None
        self.report_source = None

    def _check_insights_install(self):
        connection_test_command = self.insights_command.test_connection()
        process = subprocess.Popen(connection_test_command,
                                   stderr=subprocess.PIPE)
        streamdata = format_subprocess_stderr(process)
        code = process.returncode
        install_check = check_insights_install(streamdata)
        if not install_check or code is not 0:
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
        if not version_check['results'] or code is not 0:
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
        CliCommand._validate_args(self)
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
            self.report_source = 'scan job id(%s).' % self.args.scan_job_id
        else:
            self.report_id = self.args.report_id
            self.report_source = 'id (%s).' % self.args.report_id
        if self.args.dev:
            self.insights_command = InsightsCommands(dev=True)
        else:
            self.insights_command = InsightsCommands()
        self._check_insights_install()
        self._check_insights_version()
        print(_(messages.INSIGHTS_IS_VERIFIED))
        try:
            validate_write_file(self.tmp_tar_name, 'tmp_tar_name')
        except ValueError as error:
            print(error)
            sys.exit(1)
        print(_(messages.INSIGHTS_RETRIEVING_REPORT % self.report_source))

    def _build_req_params(self):
        self.req_path = '%s%s%s' % (
            insights.REPORT_URI,
            str(self.report_id),
            insights.DEPLOYMENTS_PATH_SUFFIX)

    def _handle_response_success(self):
        write_file(self.tmp_tar_name,
                   self.response.content,
                   True)
        upload_command = self.insights_command.upload(self.tmp_tar_name)
        process = subprocess.Popen(upload_command, stderr=subprocess.PIPE)
        streamdata = format_subprocess_stderr(process)
        code = process.returncode
        report_check = check_successful_upload(streamdata)
        if not report_check or code is not 0:
            print(_(messages.BAD_INSIGHTS_UPLOAD % (' '.join(upload_command))))
            os.remove(self.tmp_tar_name)
            sys.exit(1)
        else:
            print(_(messages.GOOD_INSIGHTS_UPLOAD %
                    (streamdata)))
            os.remove(self.tmp_tar_name)

    def _handle_response_error(self):
        print(_(messages.INSIGHTS_REPORT_NOT_FOUND % (self.args.report_id)))
        sys.exit(1)
