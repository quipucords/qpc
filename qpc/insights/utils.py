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
"""Utilities for the insights module."""

from __future__ import print_function

# pylint: disable=no-name-in-module,import-error
from distutils.version import LooseVersion

from qpc import messages
from qpc.translation import _
from qpc.utils import extract_json_from_tarfile


class InsightsCommands():
    """Creates insights-client commands for qpc client."""

    def __init__(self, dev=False):
        """Set class variables.

        Args:
            dev (bool): used to build dev insights commands for local use.
        """
        self.dev = dev
        # mime type for QPC report data for uploading to insights
        self.content_type = 'application/vnd.redhat.qpc.deployments+tgz'

    def build_base(self):
        """Will create a base used for creating insights commands."""
        if self.dev:
            return ['sudo',
                    'EGG=/etc/insights-client/rpm.egg',
                    'BYPASS_GPG=True',
                    'insights-client',
                    '--no-gpg']
        return ['sudo',
                'insights-client']

    def upload(self, tar_name):
        """Will create a command for uploading tar.gz files to insights."""
        upload_command = self.build_base()
        upload_command.append('--payload=' + tar_name)
        upload_command.append('--content-type=' + self.content_type)
        return upload_command

    def test_connection(self):
        """Will create a command that can test the connection to insights."""
        test_command = self.build_base()
        test_command.append('--test-connection')
        return test_command

    def version(self):
        """Will create a command that gathers versions."""
        version_command = self.build_base()
        version_command.append('--version')
        return version_command


def check_insights_install(streamdata):
    """Will check stream data for failure clause."""
    failures = ['FAILURE',
                'command not found',
                'No module named \'insights\'']
    require_success = 'Connectivity tests completed successfully'
    for fail in failures:
        if fail in str(streamdata):
            return False
    if require_success in str(streamdata):
        return True
    return False


def check_successful_upload(streamdata):
    """Will check stream data for success clause."""
    success = 'Successfully uploaded report'
    if success in str(streamdata):
        return True
    return False


def check_insights_version(streamdata, required_client, required_core):
    """Will check versions in streamdata to match requirements."""
    check = dict()
    stream_info = dict()
    check['results'] = True
    required_types = ['client', 'core']
    for value in streamdata.split('\n'):
        try:
            insights_type, insights_version = \
                value.replace(' ', '').lower().split(':')
            if insights_type in required_types:
                stream_info[insights_type] = insights_version
        except ValueError:
            pass
    if sorted(stream_info.keys()) != sorted(required_types):
        error_msg = 'Could not find versions for client or core.'
        return {'error': error_msg, 'results': False}
    for stream_type in required_types:
        stream_version = stream_info[stream_type]
        requirement = \
            required_client if stream_type == 'client' else required_core
        if LooseVersion(stream_version) < LooseVersion(requirement):
            check[stream_type] = stream_version
            check['results'] = False
    return check


def format_subprocess_stderr(process):
    """Will search the subprocess for the byte string and format it."""
    info_tuple = process.communicate()
    byte_string = None
    for result in info_tuple:
        if result:
            byte_string = result.decode('utf-8').strip('\n')
    return byte_string


def format_upload_success(streamdata):
    """Will parse the streamdata to retrieve helpful output."""
    try:
        stream_list = streamdata.split('\n')
        return stream_list[2]
    except IndexError:
        return streamdata


def verify_report_details(filename):
    """
    Verify that the report contents are a valid deployments report.

    :returns boolean regarding report validity
    """
    valid = True
    report_contents = extract_json_from_tarfile(filename)

    # validate report_platform_id
    report_platform_id = report_contents.get('report_platform_id')
    if not report_platform_id:
        valid = False
        print(_(messages.INSIGHTS_REPORT_MISSING_FIELD % 'report_platform_id'))

    # validate report id
    report_id = report_contents.get('report_id')
    if not report_id:
        valid = False
        print(_(messages.INSIGHTS_REPORT_MISSING_FIELD % 'report_id'))

    # validate version type
    report_version = report_contents.get('report_version')
    if not report_version:
        valid = False
        print(_(messages.INSIGHTS_REPORT_MISSING_FIELD % 'report_version'))

    # validate report type
    report_type = report_contents.get('report_type', '')
    if report_type != 'deployments':
        valid = False
        print(_(messages.INSIGHTS_MISSING_OR_INVALID % 'report_type'))

    # validate system fingerprints
    fingerprints = report_contents.get('system_fingerprints')
    if not fingerprints:
        valid = False
        print((messages.INSIGHTS_REPORT_MISSING_FIELD % 'system_fingerprints'))

    if fingerprints and report_platform_id:
        verified_fingerprints = verify_report_fingerprints(fingerprints, report_id)
        if not verified_fingerprints:
            valid = False
            print(_(messages.INSIGHTS_REPORT_NO_VALID_FP % report_id))
    return valid


def verify_report_fingerprints(fingerprints, report_id):
    """Verify that report fingerprints contain canonical facts."""
    canonical_facts = ['insights_client_id', 'bios_uuid', 'ip_addresses',
                       'mac_addresses', 'vm_uuid', 'etc_machine_id',
                       'subscription_manager_id']
    verified_fingerprints = []
    for fingerprint in fingerprints:
        found_facts = False
        for fact in canonical_facts:
            if fingerprint.get(fact):
                found_facts = True
                break
        if found_facts:
            verified_fingerprints.append(fingerprint)
        else:
            print(_(messages.INSIGHTS_REPORT_INVALID_FP %
                    (report_id, fingerprint.pop('metadata', None))))
    return verified_fingerprints
