"""Test the "vault clear" command."""

import logging
from argparse import ArgumentParser, Namespace

import pytest
import requests
import requests_mock

from qpc import messages, vault
from qpc.request import CONNECTION_ERROR_MSG
from qpc.tests.utilities import DEFAULT_CONFIG
from qpc.utils import get_server_location, write_server_config
from qpc.vault.clear import VaultClearCommand


@pytest.mark.usefixtures("server_config")
class TestVaultClearCli:
    """Class for testing the vault clear command for qpc."""

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = VaultClearCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)

    def test_clear_vault_success(self, caplog):
        """Test successfully clearing vault configuration."""
        url = get_server_location() + vault.VAULT_URI

        with requests_mock.Mocker() as mocker:
            mocker.delete(url, status_code=204)
            args = Namespace()
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.VAULT_CLEARED in caplog.text

    def test_clear_vault_ssl_err(self, caplog):
        """Test clearing vault configuration with SSL error."""
        url = get_server_location() + vault.VAULT_URI
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }

        with requests_mock.Mocker() as mocker:
            mocker.delete(url, exc=requests.exceptions.SSLError)
            args = Namespace()
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected_error in caplog.text

    def test_clear_vault_conn_err(self, caplog):
        """Test clearing vault configuration with connection error."""
        url = get_server_location() + vault.VAULT_URI
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }

        with requests_mock.Mocker() as mocker:
            mocker.delete(url, exc=requests.exceptions.ConnectTimeout)
            args = Namespace()
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected_error in caplog.text

    def test_clear_vault_internal_err(self, caplog):
        """Test clearing vault configuration with internal server error."""
        url = get_server_location() + vault.VAULT_URI
        error_message = "Server Error"

        with requests_mock.Mocker() as mocker:
            mocker.delete(url, status_code=500, json={"error": [error_message]})
            args = Namespace()
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert error_message in caplog.text

    def test_clear_vault_not_found(self, caplog):
        """Test clearing vault configuration that doesn't exist."""
        url = get_server_location() + vault.VAULT_URI
        error_message = "Not found."

        with requests_mock.Mocker() as mocker:
            mocker.delete(
                url,
                status_code=404,
                json={"detail": error_message},
            )
            args = Namespace()
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert error_message in caplog.text

    def test_clear_vault_unauthorized(self, caplog):
        """Test clearing vault configuration with unauthorized error."""
        url = get_server_location() + vault.VAULT_URI
        error_message = "Authentication credentials were not provided."

        with requests_mock.Mocker() as mocker:
            mocker.delete(
                url,
                status_code=401,
                json={"detail": error_message},
            )
            args = Namespace()
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert error_message in caplog.text

    def test_clear_vault_forbidden(self, caplog):
        """Test clearing vault configuration with forbidden error."""
        url = get_server_location() + vault.VAULT_URI
        error_message = "You do not have permission to perform this action."

        with requests_mock.Mocker() as mocker:
            mocker.delete(
                url,
                status_code=403,
                json={"detail": error_message},
            )
            args = Namespace()
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert error_message in caplog.text
