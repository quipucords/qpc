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
from shutil import copyfile

import qpc.insights as insights
from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.insights.utils import (InsightsCommands,
                                check_insights_install,
                                check_insights_version,
                                check_successful_upload,
                                format_subprocess_stderr,
                                format_upload_success)
from qpc.release import VERSION
from qpc.request import GET, request
from qpc.translation import _
from qpc.utils import (validate_write_file,
                       write_file)

# pylint: disable=no-name-in-module,import-error
from requests import codes

CANONICAL_FACTS = ['bios_uuid', 'etc_machine_id', 'insights_client_id',
                   'ip_addresses', 'mac_addresses',
                   'subscription_manager_id', 'vm_uuid']


def verify_report_hosts(hosts):
    """Verify that report hosts contain canonical facts.

    :param hosts: dictionary of hosts to verify
    returns: (dicts) valid, invalid hosts
    """
    valid_hosts = {}
    invalid_hosts = {}
    for host_id, host in hosts.items():
        found_facts = False
        for fact in CANONICAL_FACTS:
            if host.get(fact):
                found_facts = True
                break
        if found_facts:
            valid_hosts[host_id] = host
        else:
            invalid_hosts[host_id] = host

    return valid_hosts, invalid_hosts


class InsightsUploadCommand(CliCommand):
    """Defines the Insights command.

    This command is for uploading QPC reports throught the insights client.
    """

    # pylint: disable=too-few-public-methods
    SUBCOMMAND = insights.SUBCOMMAND
    ACTION = insights.UPLOAD

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(self, self.SUBCOMMAND, self.ACTION,
                            subparsers.add_parser(self.ACTION), GET,
                            insights.REPORT_URI, [codes.ok])
        input_group = self.parser.add_mutually_exclusive_group(required=True)
        input_group.add_argument('--report', dest='report_id',
                                 metavar='REPORT_ID',
                                 help=_(messages.INSIGHTS_REPORT_ID_HELP))
        input_group.add_argument('--scan-job', dest='scan_job_id',
                                 metavar='SCAN_JOB_ID',
                                 help=_(messages.INSIGHTS_SCAN_JOB_ID_HELP))
        input_group.add_argument('--gzip-file', dest='gzip_file', metavar='GZIP_FILE',
                                 help=_(messages.INSIGHTS_INPUT_GZIP_HELP))

        self.parser.add_argument('--no-gpg', dest='no_gpg', action='store_true',
                                 help=_(messages.INSIGHTS_NO_GPG_HELP))
        self.tmp_tar_name = '/tmp/insights_tmp_%s.tar.gz' % (
            time.strftime('%Y%m%d_%H%M%S'))
        self.min_server_version = VERSION
        self.insights_command = None
        self.report_id = None

    def _check_insights_install(self):
        connection_test_command = self.insights_command.test_connection()
        process = subprocess.Popen(connection_test_command,
                                   stderr=subprocess.PIPE)
        streamdata = format_subprocess_stderr(process)
        install_check = check_insights_install(streamdata)
        if not install_check:
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

        # Validate target report output location
        try:
            validate_write_file(self.tmp_tar_name, 'tmp_tar_name')
        except ValueError:
            print(_(messages.INSIGHTS_TMP_ERROR % self.tmp_tar_name))
            sys.exit(1)

        # Validate Insights client
        if self.args.no_gpg:
            self.insights_command = InsightsCommands(no_gpg=True)
        else:
            self.insights_command = InsightsCommands()
        self._check_insights_install()
        self._check_insights_version()
        print(_(messages.INSIGHTS_IS_VERIFIED))

        # obtaining the report as tar.gz
        if self.args.gzip_file:
            self._obtain_insights_report_from_local_file()
        else:
            self._obtain_insights_report_from_qpc_server()

    def _obtain_insights_report_from_local_file(self):
        """Load local report, validate, and write tar.gz."""
        gzip_file = self.args.gzip_file
        if not os.path.isfile(gzip_file):
            print(_(messages.INSIGHTS_LOCAL_REPORT_NOT % gzip_file))
            sys.exit(1)

        copyfile(self.args.gzip_file, self.tmp_tar_name)

    def _obtain_insights_report_from_qpc_server(self):
        """Download report, validate, and write tar.gz."""
        # Obtain report ID
        self.report_id = None
        if self.args.report_id is None:
            # Make request to convert scan_job_id to self.report_id
            scan_job_response = request(parser=self.parser, method=GET,
                                        path='%s%s' % (scan.SCAN_JOB_URI,
                                                       self.args.scan_job_id),
                                        payload=None)
            if scan_job_response.status_code == codes.ok:  # pylint: disable=no-member
                json_data = scan_job_response.json()
                self.report_id = json_data.get('report_id')
                if self.report_id is None:
                    print(_(messages.REPORT_NO_DEPLOYMENTS_REPORT_FOR_SJ %
                            self.args.scan_job_id))
                    sys.exit(1)
            else:
                print(_(messages.REPORT_SJ_DOES_NOT_EXIST %
                        self.args.scan_job_id))
                sys.exit(1)

            # Log report ID that was obtained from scanjob
            print(_(messages.INSIGHTS_SCAN_JOB_ID_PRODUCED %
                    (self.args.scan_job_id,
                     self.report_id)))
        else:
            self.report_id = self.args.report_id

        # Request report from QCP server
        print(_(messages.INSIGHTS_RETRIEVE_REPORT % self.report_id))
        headers = {'Accept': 'application/gzip'}
        report_path = '%s%s%s' % (
            insights.REPORT_URI,
            str(self.report_id),
            insights.INSIGHTS_PATH_SUFFIX)
        report_response = request(parser=self.parser,
                                  method=GET,
                                  path=report_path,
                                  headers=headers,
                                  payload=None,
                                  min_server_version=VERSION)

        if report_response.status_code != codes.ok:  # pylint: disable=no-member
            print(_(messages.INSIGHTS_REPORT_NOT_FOUND %
                    self.report_id))
            sys.exit(1)

        # write file content to disk
        write_file(self.tmp_tar_name,
                   report_response.content,
                   True)

    def _do_command(self):
        """Execute command flow.

        Sub-commands define this method to perform the
        required action once all options have been verified.
        """
        # This command doesn't follow pattern so we just jump to success
        self._upload_to_insights()

    def _upload_to_insights(self):
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

        format_streamdata = format_upload_success(streamdata)
        print(_(format_streamdata))
        os.remove(self.tmp_tar_name)
