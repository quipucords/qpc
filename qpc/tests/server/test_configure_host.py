"""Test the CLI module."""

import logging
import sys

import pytest

from qpc import messages
from qpc.cli import CLI
from qpc.tests.utilities import HushUpStderr
from qpc.utils import read_server_config, write_server_config

DEFAULT_PORT = 9443


class TestConfigureHost:
    """Class for testing the server host configuration."""

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        """Inject caplog as we need to use it during teardown."""
        self._caplog = caplog

    def setup_method(self, _test_method):
        """Create test setup."""
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def teardown_method(self, _test_method):
        """Remove test case setup."""
        # Reset server config to default ip/port
        sys.argv = [
            "/bin/qpc",
            "server",
            "config",
            "--host",
            "127.0.0.1",
            "--port",
            str(DEFAULT_PORT),
        ]

        with self._caplog.at_level(logging.INFO):
            CLI().main()
            config = read_server_config()
            assert config["host"] == "127.0.0.1"
            assert config["port"] == DEFAULT_PORT
            expected_message = messages.SERVER_CONFIG_SUCCESS % {
                "protocol": "https",
                "host": "127.0.0.1",
                "port": str(DEFAULT_PORT),
            }
            assert expected_message in self._caplog.text
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_config_host_req_args_err(self):
        """Testing the configure server requires host arg."""
        with pytest.raises(SystemExit):
            sys.argv = ["/bin/qpc", "server", "config"]
            CLI().main()

    def test_config_host_alpha_port_err(self):
        """Testing the configure server requires bad port."""
        with pytest.raises(SystemExit):
            sys.argv = [
                "/bin/qpc",
                "server",
                "config",
                "--host",
                "127.0.0.1",
                "--port",
                "abc",
            ]
            CLI().main()

    def test_success_config_server(self, caplog):
        """Testing the configure server green path."""
        sys.argv = [
            "/bin/qpc",
            "server",
            "config",
            "--host",
            "127.0.0.1",
            "--port",
            "8005",
        ]
        with caplog.at_level(logging.INFO):
            CLI().main()
            config = read_server_config()
            assert config["host"] == "127.0.0.1"
            assert config["port"] == 8005
            expected_message = messages.SERVER_CONFIG_SUCCESS % {
                "protocol": "https",
                "host": "127.0.0.1",
                "port": "8005",
            }
            assert expected_message in caplog.text

    def test_config_server_default_port(self):
        """Testing the configure server default port."""
        sys.argv = ["/bin/qpc", "server", "config", "--host", "127.0.0.1"]
        CLI().main()
        config = read_server_config()
        assert config["host"] == "127.0.0.1"
        assert config["port"] == DEFAULT_PORT

    def test_invalid_configuration(self):
        """Test reading bad JSON on cli start."""
        write_server_config({})

        sys.argv = ["/bin/qpc", "server", "config", "--host", "127.0.0.1"]
        CLI().main()
        config = read_server_config()
        assert config["host"] == "127.0.0.1"
        assert config["port"] == DEFAULT_PORT

    def test_run_command_no_config(self):
        """Test running command without config."""
        write_server_config({})

        with pytest.raises(SystemExit):
            sys.argv = ["/bin/qpc", "cred"]
            CLI().main()
