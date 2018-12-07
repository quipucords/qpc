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
"""Test the utils module."""

import os
import time
import unittest

from qpc import utils
from qpc.tests_utilities import create_tar_buffer


class UtilsTests(unittest.TestCase):
    """Class for testing the utils module qpc."""

    def setUp(self):
        """Set up the class variables."""
        self.report_json = {
            'report_id': 1,
            'report_type': 'deployments',
            'report_version': '1.0.0.1b025b8',
            'status': 'completed',
            'report_platform_id': '5f2cc1fd-ec66-4c67-be1b-171a595ce319',
            'system_fingerprints': [{'bios_uuid': 'value'}]}
        self.test_file = {'test.json': self.report_json}
        self.tmp_tar = 'test_%d.tar.gz' % time.time()

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        try:
            os.remove(self.tmp_tar)
        except FileNotFoundError:
            pass

    def create_tarfile(self):
        """Create a tarfile to test the extract json from tarfile method."""
        utils.write_file(self.tmp_tar, create_tar_buffer(self.test_file), True)

    def test_read_client_token(self):
        """Testing the read client token function."""
        check_value = False
        if not os.path.exists(utils.QPC_CLIENT_TOKEN):
            check_value = True
            expected_token = '100'
            token_json = {'token': expected_token}
            utils.write_client_token(token_json)
        token = utils.read_client_token()
        self.assertTrue(isinstance(token, str))
        if check_value:
            self.assertEqual(token, expected_token)

    def test_extract_json_from_tarfile(self):
        """Test extracting json from tarfile."""
        self.create_tarfile()
        json = utils.extract_json_from_tarfile(self.tmp_tar)
        self.assertEqual(json, self.report_json)
