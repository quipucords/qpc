"""Test the CLI module."""

import sys
import unittest

from qpc.cli import CLI
from qpc.utils import (
    read_insights_login_config,
    write_insights_login_config,
    write_server_config,
)


class InsightsAddLoginTests(unittest.TestCase):
    """Class for testing insights add login command."""

    def setUp(self):
        """Create test setup."""
        # All cli commands require qpc config and qpc login to be executed,
        # require_token must be False, so we don't have to pass login info
        write_server_config(
            {
                "host": "127.0.0.1",
                "port": 8000,
                "use_http": True,
                "require_token": False,
            }
        )

    def test_insight_login_req_args_err(self):
        """Testing if insights add-login command requires args."""
        sys.argv = ["/bin/qpc", "insights", "add_login"]
        with self.assertRaises(SystemExit):
            CLI().main()

    def test_insights_config_bad_username(self):
        """Testing insights configure when receiving bad username."""
        sys.argv = ["/bin/qpc", "insights", "add-login", "--username", None]
        with self.assertRaises(SystemExit):
            CLI().main()

    def test_insights_config_empty_username(self):
        """Testing insights configure when receiving bad username."""
        sys.argv = ["/bin/qpc", "insights", "add-login", "--username", ""]
        with self.assertRaises(SystemExit):
            CLI().main()

    def test_insights_config_bad_password(self):
        """Testing insights configure when receiving bad username."""
        sys.argv = ["/bin/qpc", "insights", "add-login", "--password", None]
        with self.assertRaises(SystemExit):
            CLI().main()

    def test_insights_config_empty_password(self):
        """Testing insights configure when receiving bad username."""
        sys.argv = ["/bin/qpc", "insights", "add-login", "--password", ""]
        with self.assertRaises(SystemExit):
            CLI().main()

    def test_success_add_insights_login_config(self):
        """Testing insights login config green path."""
        sys.argv = [
            "/bin/qpc",
            "insights",
            "add_login",
            "--username",
            "insights-test-user",
            "--password",
            "insights-test-password",
        ]
        CLI().main()
        config = read_insights_login_config()
        self.assertEqual(config["username"], "insights-test-user")
        self.assertEqual(config["password"], "insights-test-password")

    def test_run_command_no_config(self):
        """Test running command without config."""
        write_insights_login_config({})
        sys.argv = ["/bin/qpc", "insights", "add_login"]
        with self.assertRaises(SystemExit):
            CLI().main()
