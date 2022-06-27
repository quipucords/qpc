"""Test the CLI module."""
import os
import sys
import unittest

from qpc import utils
from qpc.cli import CLI
from qpc.utils import (
    DEFAULT_HOST_INSIGHTS_CONFIG,
    DEFAULT_INSIGHTS_CONFIG,
    DEFAULT_PORT_INSIGHTS_CONFIG,
    DEFAULT_USE_HTTP_INSIGHTS_CONFIG,
    read_insights_config,
    write_insights_config,
    write_server_config,
)


class InsightsConfigureTests(unittest.TestCase):
    """Class for testing insights host configuration."""

    def setUp(self):
        """Create test setup."""
        write_server_config(
            {
                "host": "127.0.0.1",
                "port": 8000,
                "use_http": True,
                "require_token": False,
            }
        )

    def test_insights_config_bad_port(self):
        """Testing insights configure when receiving bad port."""
        sys.argv = ["/bin/qpc", "insights", "config", "--port", "abc"]
        with self.assertRaises(SystemExit):
            CLI().main()

    def test_insights_config_empty_host(self):
        """Testing insights configure when receiving bad host."""
        sys.argv = ["/bin/qpc", "insights", "config", "--host", ""]
        with self.assertRaises(SystemExit):
            CLI().main()

    def test_insights_config_bad_host(self):
        """Testing insights configure when receiving bad host."""
        sys.argv = ["/bin/qpc", "insights", "config", "--host", None]
        with self.assertRaises(SystemExit):
            CLI().main()

    def test_success_default_config_no_args(self):
        """Testing if method returns default config dict when no arguments."""
        config = read_insights_config()
        self.assertDictEqual(config, DEFAULT_INSIGHTS_CONFIG)
        self.assertFalse(os.path.exists(utils.INSIGHTS_CONFIG))

    def test_success_config_insights(self):
        """Testing insights configure green path."""
        sys.argv = [
            "/bin/qpc",
            "insights",
            "config",
            "--host",
            "console.insights.test",
            "--port",
            "200",
            "--use-http",
        ]
        CLI().main()
        config = read_insights_config()
        self.assertEqual(config["host"], "console.insights.test")
        self.assertEqual(config["port"], 200)
        self.assertEqual(config["use_http"], True)

    def test_insights_config_default_host(self):
        """Testing insights configure default host."""
        sys.argv = ["/bin/qpc", "insights", "config", "--port", "200"]
        CLI().main()
        config = read_insights_config()
        self.assertEqual(config["host"], DEFAULT_HOST_INSIGHTS_CONFIG)
        self.assertEqual(config["port"], 200)
        self.assertEqual(config["use_http"], DEFAULT_USE_HTTP_INSIGHTS_CONFIG)

    def test_insights_config_default_port(self):
        """Testing insights configure default port."""
        sys.argv = ["/bin/qpc", "insights", "config", "--host", "console.insights.test"]
        CLI().main()
        config = read_insights_config()
        self.assertEqual(config["host"], "console.insights.test")
        self.assertEqual(config["port"], DEFAULT_PORT_INSIGHTS_CONFIG)
        self.assertEqual(config["use_http"], DEFAULT_USE_HTTP_INSIGHTS_CONFIG)

    def test_invalid_configuration(self):
        """Test reading bad JSON on cli start."""
        write_insights_config({})

        config = read_insights_config()
        self.assertEqual(config["host"], DEFAULT_HOST_INSIGHTS_CONFIG)
        self.assertEqual(config["port"], DEFAULT_PORT_INSIGHTS_CONFIG)
        self.assertEqual(config["use_http"], DEFAULT_USE_HTTP_INSIGHTS_CONFIG)
