"""Test the "vault show" command."""

import io
import json
import logging
from argparse import ArgumentParser, Namespace

import pytest
import requests
import requests_mock

from qpc import messages, vault
from qpc.request import CONNECTION_ERROR_MSG
from qpc.tests.utilities import DEFAULT_CONFIG, redirect_stdout
from qpc.utils import get_server_location, write_server_config
from qpc.vault.show import VaultShowCommand


@pytest.mark.usefixtures("server_config")
class TestVaultShowCli:
    """Class for testing the vault show command for qpc."""

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = VaultShowCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)

    def test_show_vault_success(self):
        """Test successfully showing vault configuration."""
        url = get_server_location() + vault.VAULT_URI

        vault_data = {
            "address": "vault.example.com",
            "port": 8200,
            "ssl_verify": True,
        }

        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=vault_data)
            args = Namespace()
            output = io.StringIO()
            with redirect_stdout(output):
                self.command.main(args)
            result = output.getvalue()
            result_json = json.loads(result)
            assert result_json == vault_data

    def test_show_vault_with_all_fields(self):
        """Test showing vault configuration with all fields."""
        url = get_server_location() + vault.VAULT_URI

        vault_data = {
            "address": "vault.example.com",
            "port": 9200,
            "ssl_verify": False,
        }

        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=vault_data)
            args = Namespace()
            output = io.StringIO()
            with redirect_stdout(output):
                self.command.main(args)
            result = output.getvalue()
            result_json = json.loads(result)
            assert result_json == {
                "address": "vault.example.com",
                "port": 9200,
                "ssl_verify": False,
            }

    def test_show_vault_invalid_json(self, caplog):
        """Test showing vault configuration with invalid JSON response."""
        url = get_server_location() + vault.VAULT_URI

        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, text="not valid json")
            args = Namespace()
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert messages.VAULT_INVALID_JSON_RESPONSE in caplog.text

    def test_show_vault_ssl_err(self, caplog):
        """Test showing vault configuration with SSL error."""
        url = get_server_location() + vault.VAULT_URI
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }

        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            args = Namespace()
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert expected_error in caplog.text

    def test_show_vault_conn_err(self, caplog):
        """Test showing vault configuration with connection error."""
        url = get_server_location() + vault.VAULT_URI
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }

        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            args = Namespace()
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert expected_error in caplog.text

    def test_show_vault_internal_err(self, caplog):
        """Test showing vault configuration with internal server error."""
        url = get_server_location() + vault.VAULT_URI
        error_message = "Server Error"

        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={"error": [error_message]})
            args = Namespace()
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert error_message in caplog.text

    def test_show_vault_not_found(self, caplog):
        """Test showing vault configuration that doesn't exist."""
        url = get_server_location() + vault.VAULT_URI
        error_message = "Not found."

        with requests_mock.Mocker() as mocker:
            mocker.get(
                url,
                status_code=404,
                json={"detail": error_message},
            )
            args = Namespace()
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert error_message in caplog.text

    def test_show_vault_unauthorized(self, caplog):
        """Test showing vault configuration with unauthorized error."""
        url = get_server_location() + vault.VAULT_URI
        error_message = "Authentication credentials were not provided."

        with requests_mock.Mocker() as mocker:
            mocker.get(
                url,
                status_code=401,
                json={"detail": error_message},
            )
            args = Namespace()
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert error_message in caplog.text

    def test_show_vault_empty_response(self):
        """Test showing vault configuration with empty response."""
        url = get_server_location() + vault.VAULT_URI

        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={})
            args = Namespace()
            output = io.StringIO()
            with redirect_stdout(output):
                self.command.main(args)
            result = output.getvalue()
            result_json = json.loads(result)
            assert result_json == {}

    def test_show_vault_formatted_output(self):
        """Test that vault show output is properly formatted JSON."""
        url = get_server_location() + vault.VAULT_URI

        vault_data = {
            "address": "vault.example.com",
            "port": 8200,
            "ssl_verify": True,
        }

        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=vault_data)
            args = Namespace()
            output = io.StringIO()
            with redirect_stdout(output):
                self.command.main(args)
            result = output.getvalue()
            # Verify it's properly formatted (has newlines and indentation)
            assert "{\n" in result
            assert "    " in result  # indentation
            # Verify it can be parsed
            result_json = json.loads(result)
            assert result_json == vault_data
