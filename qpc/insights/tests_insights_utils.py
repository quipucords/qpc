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

import unittest

from qpc.insights.utils import (
    InsightsCommands,
    check_insights_install,
    check_insights_version,
    check_successful_upload,
)


class InsightsUploadCliTests(unittest.TestCase):
    """Class for testing the validation for install of insights-client."""

    def setUp(self):
        """Create test setup."""

    def tearDown(self):
        """Remove test setup."""

    def test_check_insights_install(self):
        """Testing if insights is installed correctly."""
        # pylint:disable=line-too-long
        successful_install = "Could not reach the Insights service to register.\nRunning connection test...\nConnection test config:\n=== Begin Certificate Chain Test ===\ndepth=1\nverify error:num=0\nverify return:1\ndepth=0\nverify error:num=0\nverify return:1\n=== End Certificate Chain Test: SUCCESS ===\n\n=== Begin Upload URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: \nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/uploads/\n=== End Upload URL Connection Test: SUCCESS ===\n\n=== Begin API URL Connection Test ===\nHTTP Status Code: 200\nHTTP Status Text: OK\nHTTP Response Text: lub-dub\nSuccessfully connected to: https://cert-api.access.redhat.com/r/insights/\n=== End API URL Connection Test: SUCCESS ===\n\n\nConnectivity tests completed successfully\nSee /var/log/insights-client/insights-client.log for more details.\n"  # noqa: E501
        test = check_insights_install(successful_install)
        self.assertEqual(test, True)

    def test_check_insights_install_error_no_command(self):
        """Testing error response no command found."""
        no_command_return = "insights-client: command not found"
        test = check_insights_install(no_command_return)
        self.assertEqual(test, False)

    def test_check_insights_install_no_module(self):
        """Testing error response no modules found."""
        no_module_return = "ModuleNotFoundError: No module named 'insights'"
        test = check_insights_install(no_module_return)
        self.assertEqual(test, False)

    def test_check_insights_version_failed(self):
        """Testing failed response with out-of-date client versions."""
        old_versions = ["3.0.0-4", "3.0.2-2", "3.0.1-5"]
        for version in old_versions:
            streamdata = f"Client: {version}\nCore: 3.0.8-1"
            result = check_insights_version(streamdata, "3.0.3-1", "3.0.8")
            self.assertIn("client", result.keys())

    def test_check_insights_version_success(self):
        """Testing success response with new client versions."""
        new_versions = ["3.0.0-4", "3.0.2-2", "3.0.1-5", "3.0.3-1"]
        for version in new_versions:
            streamdata = f"Client: {version}\nCore: 3.0.8-1"
            result = check_insights_version(streamdata, "3.0.0-4", "3.0.8")
            self.assertNotIn("client", result.keys())

    def test_no_gpg_base_command_build(self):
        """Test if no_gpg flag adds required data to insights command."""
        init_insights = InsightsCommands(no_gpg=True)
        command = init_insights.build_base()
        no_gpg_required = ["BYPASS_GPG=True", "--no-gpg"]
        for item in no_gpg_required:
            self.assertIn(item, command)

    def test_unsuccessful_upload_return(self):
        """Test is unsuccessful upload returns False."""
        unsuccessful_msg = b"Report not uploaded."
        result = check_successful_upload(unsuccessful_msg)
        self.assertEqual(result, False)
