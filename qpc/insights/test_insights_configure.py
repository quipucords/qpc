"""Test the CLI module."""
import sys
from unittest import mock

import pytest

from qpc import utils
from qpc.cli import CLI
from qpc.utils import (
    DEFAULT_HOST_INSIGHTS_CONFIG,
    DEFAULT_INSIGHTS_CONFIG,
    DEFAULT_PORT_INSIGHTS_CONFIG,
    DEFAULT_SSO_HOST_INSIGHTS_CONFIG,
    DEFAULT_USE_HTTP_INSIGHTS_CONFIG,
    read_insights_config,
    write_insights_config,
)


class TestInsightsConfigure:
    """Class for testing insights host configuration."""

    def test_insights_config_bad_port(self):
        """Testing insights configure when receiving bad port."""
        test_argv = ["/bin/qpc", "insights", "config", "--port", "abc"]
        with pytest.raises(SystemExit), mock.patch.object(sys, "argv", test_argv):
            CLI().main()

    def test_insights_config_empty_host(self):
        """Testing insights configure when receiving empty host."""
        test_argv = ["/bin/qpc", "insights", "config", "--host", ""]
        with pytest.raises(SystemExit), mock.patch.object(sys, "argv", test_argv):
            CLI().main()

    def test_insights_config_bad_host(self):
        """Testing insights configure when receiving bad host."""
        test_argv = ["/bin/qpc", "insights", "config", "--host", None]
        with pytest.raises(SystemExit), mock.patch.object(sys, "argv", test_argv):
            CLI().main()

    def test_insights_config_bad_sso_host(self):
        """Testing insights configure when receiving bad sso host."""
        test_argv = ["/bin/qpc", "insights", "config", "--sso-host", None]
        with pytest.raises(SystemExit), mock.patch.object(sys, "argv", test_argv):
            CLI().main()

    def test_success_default_config_no_args(self):
        """Testing if method returns default config dict when no arguments."""
        config = read_insights_config()
        assert config == DEFAULT_INSIGHTS_CONFIG
        assert not utils.INSIGHTS_CONFIG.exists()

    def test_success_config_insights(self):
        """Testing insights configure green path."""
        test_argv = [
            "/bin/qpc",
            "insights",
            "config",
            "--host",
            "console.insights.test",
            "--port",
            "200",
            "--use-http",
        ]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        config = read_insights_config()
        assert config["host"] == "console.insights.test"
        assert config["port"] == 200
        assert config["use_http"]

    def test_success_config_insights_with_sso_host(self):
        """Testing insights configure green path with sso host."""
        test_argv = [
            "/bin/qpc",
            "insights",
            "config",
            "--host",
            "console.insights.test",
            "--port",
            "200",
            "--use-http",
            "--sso-host",
            "sso.insights.test",
        ]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        config = read_insights_config()
        assert config["host"] == "console.insights.test"
        assert config["port"] == 200
        assert config["use_http"]
        assert config["sso_host"] == "sso.insights.test"

    def test_insights_config_default_host(self):
        """Testing insights configure default host."""
        test_argv = ["/bin/qpc", "insights", "config", "--port", "200"]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        config = read_insights_config()
        assert config["host"] == DEFAULT_HOST_INSIGHTS_CONFIG
        assert config["port"] == 200
        assert config["use_http"] == DEFAULT_USE_HTTP_INSIGHTS_CONFIG

    def test_insights_config_default_port(self):
        """Testing insights configure default port."""
        test_argv = [
            "/bin/qpc",
            "insights",
            "config",
            "--host",
            "console.insights.test",
        ]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        config = read_insights_config()
        assert config["host"] == "console.insights.test"
        assert config["port"] == DEFAULT_PORT_INSIGHTS_CONFIG
        assert config["use_http"] == DEFAULT_USE_HTTP_INSIGHTS_CONFIG

    def test_insights_config_default_sso_host(self):
        """Testing insights configure default sso host."""
        test_argv = [
            "/bin/qpc",
            "insights",
            "config",
            "--host",
            "console.insights.test",
            "--port",
            "200",
        ]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        config = read_insights_config()
        assert config["host"] == "console.insights.test"
        assert config["port"] == 200
        assert config["use_http"] == DEFAULT_USE_HTTP_INSIGHTS_CONFIG
        assert config["sso_host"] == DEFAULT_SSO_HOST_INSIGHTS_CONFIG

    def test_invalid_configuration(self):
        """Test reading bad JSON on cli start."""
        write_insights_config({})

        config = read_insights_config()
        assert config["host"] == DEFAULT_HOST_INSIGHTS_CONFIG
        assert config["port"] == DEFAULT_PORT_INSIGHTS_CONFIG
        assert config["use_http"] == DEFAULT_USE_HTTP_INSIGHTS_CONFIG
        assert config["sso_host"] == DEFAULT_SSO_HOST_INSIGHTS_CONFIG
