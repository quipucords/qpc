"""Test the CLI module."""

import sys
from unittest import mock

import pytest

from qpc import utils
from qpc.cli import CLI
from qpc.utils import (
    DEFAULT_HOST_LIGHTSPEED_CONFIG,
    DEFAULT_LIGHTSPEED_CONFIG,
    DEFAULT_PORT_LIGHTSPEED_CONFIG,
    DEFAULT_SSO_HOST_LIGHTSPEED_CONFIG,
    DEFAULT_USE_HTTP_LIGHTSPEED_CONFIG,
    read_lightspeed_config,
    write_lightspeed_config,
)


class TestLightspeedConfigure:
    """Class for testing Lightspeed host configuration."""

    def test_lightspeed_config_bad_port(self):
        """Testing Lightspeed configure when receiving bad port."""
        test_argv = ["/bin/qpc", "lightspeed", "config", "--port", "abc"]
        with pytest.raises(SystemExit), mock.patch.object(sys, "argv", test_argv):
            CLI().main()

    def test_lightspeed_config_empty_host(self):
        """Testing Lightspeed configure when receiving empty host."""
        test_argv = ["/bin/qpc", "lightspeed", "config", "--host", ""]
        with pytest.raises(SystemExit), mock.patch.object(sys, "argv", test_argv):
            CLI().main()

    def test_lightspeed_config_bad_host(self):
        """Testing Lightspeed configure when receiving bad host."""
        test_argv = ["/bin/qpc", "lightspeed", "config", "--host", None]
        with pytest.raises(SystemExit), mock.patch.object(sys, "argv", test_argv):
            CLI().main()

    def test_lightspeed_config_bad_sso_host(self):
        """Testing Lightspeed configure when receiving bad sso host."""
        test_argv = ["/bin/qpc", "lightspeed", "config", "--sso-host", None]
        with pytest.raises(SystemExit), mock.patch.object(sys, "argv", test_argv):
            CLI().main()

    def test_success_default_config_no_args(self):
        """Testing if method returns default config dict when no arguments."""
        config = read_lightspeed_config()
        assert config == DEFAULT_LIGHTSPEED_CONFIG
        assert not utils.LIGHTSPEED_CONFIG.exists()

    def test_success_config_lightspeed(self):
        """Testing Lightspeed configure green path."""
        test_argv = [
            "/bin/qpc",
            "lightspeed",
            "config",
            "--host",
            "console.lightspeed.test",
            "--port",
            "200",
            "--use-http",
        ]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        config = read_lightspeed_config()
        assert config["host"] == "console.lightspeed.test"
        assert config["port"] == 200
        assert config["use_http"]

    def test_success_config_lightspeed_with_sso_host(self):
        """Testing Lightspeed configure green path with sso host."""
        test_argv = [
            "/bin/qpc",
            "lightspeed",
            "config",
            "--host",
            "console.lightspeed.test",
            "--port",
            "200",
            "--use-http",
            "--sso-host",
            "sso.lightspeed.test",
        ]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        config = read_lightspeed_config()
        assert config["host"] == "console.lightspeed.test"
        assert config["port"] == 200
        assert config["use_http"]
        assert config["sso_host"] == "sso.lightspeed.test"

    def test_lightspeed_config_default_host(self):
        """Testing Lightspeed configure default host."""
        test_argv = ["/bin/qpc", "lightspeed", "config", "--port", "200"]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        config = read_lightspeed_config()
        assert config["host"] == DEFAULT_HOST_LIGHTSPEED_CONFIG
        assert config["port"] == 200
        assert config["use_http"] == DEFAULT_USE_HTTP_LIGHTSPEED_CONFIG

    def test_lightspeed_config_default_port(self):
        """Testing Lightspeed configure default port."""
        test_argv = [
            "/bin/qpc",
            "lightspeed",
            "config",
            "--host",
            "console.lightspeed.test",
        ]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        config = read_lightspeed_config()
        assert config["host"] == "console.lightspeed.test"
        assert config["port"] == DEFAULT_PORT_LIGHTSPEED_CONFIG
        assert config["use_http"] == DEFAULT_USE_HTTP_LIGHTSPEED_CONFIG

    def test_lightspeed_config_default_sso_host(self):
        """Testing Lightspeed configure default sso host."""
        test_argv = [
            "/bin/qpc",
            "lightspeed",
            "config",
            "--host",
            "console.lightspeed.test",
            "--port",
            "200",
        ]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        config = read_lightspeed_config()
        assert config["host"] == "console.lightspeed.test"
        assert config["port"] == 200
        assert config["use_http"] == DEFAULT_USE_HTTP_LIGHTSPEED_CONFIG
        assert config["sso_host"] == DEFAULT_SSO_HOST_LIGHTSPEED_CONFIG

    def test_invalid_configuration(self):
        """Test reading bad JSON on cli start."""
        write_lightspeed_config({})

        config = read_lightspeed_config()
        assert config["host"] == DEFAULT_HOST_LIGHTSPEED_CONFIG
        assert config["port"] == DEFAULT_PORT_LIGHTSPEED_CONFIG
        assert config["use_http"] == DEFAULT_USE_HTTP_LIGHTSPEED_CONFIG
        assert config["sso_host"] == DEFAULT_SSO_HOST_LIGHTSPEED_CONFIG
