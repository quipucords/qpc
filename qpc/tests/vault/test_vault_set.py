"""Test the "vault set" command."""

import logging
from argparse import ArgumentParser, Namespace

import pytest
import requests
import requests_mock

from qpc import messages, vault
from qpc.request import CONNECTION_ERROR_MSG
from qpc.tests.utilities import DEFAULT_CONFIG
from qpc.utils import get_server_location, write_server_config
from qpc.vault.set import VaultSetCommand


@pytest.mark.usefixtures("server_config")
class TestVaultSetCli:
    """Class for testing the vault set command for qpc."""

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = VaultSetCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)

    def test_set_vault_success(
        self, tmp_path, test_cert_content, test_key_content, caplog
    ):
        """Test successfully setting vault configuration."""
        url = get_server_location() + vault.VAULT_URI

        # Create test certificate files
        client_cert = tmp_path / "client.pem"
        client_key = tmp_path / "client-key.pem"
        ca_cert = tmp_path / "ca.pem"

        client_cert.write_bytes(test_cert_content)
        client_key.write_bytes(test_key_content)
        ca_cert.write_bytes(test_cert_content)

        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            args = Namespace(
                address="vault.example.com",
                port=8200,
                ssl_verify="true",
                client_cert=str(client_cert),
                client_key=str(client_key),
                ca_cert=str(ca_cert),
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.VAULT_CONFIG_SUCCESS in caplog.text

    def test_set_vault_success_with_ok_status(
        self, tmp_path, test_cert_content, test_key_content, caplog
    ):
        """Test successfully setting vault configuration with 200 OK status."""
        url = get_server_location() + vault.VAULT_URI

        # Create test certificate files
        client_cert = tmp_path / "client.pem"
        client_key = tmp_path / "client-key.pem"
        ca_cert = tmp_path / "ca.pem"

        client_cert.write_bytes(test_cert_content)
        client_key.write_bytes(test_key_content)
        ca_cert.write_bytes(test_cert_content)

        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=200)
            args = Namespace(
                address="vault.example.com",
                port=8200,
                ssl_verify="true",
                client_cert=str(client_cert),
                client_key=str(client_key),
                ca_cert=str(ca_cert),
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.VAULT_CONFIG_SUCCESS in caplog.text

    def test_set_vault_without_ca_cert_when_ssl_verify_false(
        self, tmp_path, test_cert_content, caplog
    ):
        """Test setting vault configuration without CA cert when ssl_verify is false."""
        url = get_server_location() + vault.VAULT_URI

        # Create test certificate files
        client_cert = tmp_path / "client.pem"
        client_key = tmp_path / "client-key.pem"

        client_cert.write_bytes(test_cert_content)
        client_key.write_bytes(test_cert_content)

        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            args = Namespace(
                address="vault.example.com",
                port=8200,
                ssl_verify="false",
                client_cert=str(client_cert),
                client_key=str(client_key),
                ca_cert=None,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.VAULT_CONFIG_SUCCESS in caplog.text

    def test_set_vault_missing_ca_cert_when_ssl_verify_true(
        self, tmp_path, test_cert_content, test_key_content, caplog
    ):
        """Test setting vault with ssl_verify true but missing CA cert fails."""
        # Create test certificate files
        client_cert = tmp_path / "client.pem"
        client_key = tmp_path / "client-key.pem"

        client_cert.write_bytes(test_cert_content)
        client_key.write_bytes(test_key_content)

        args = Namespace(
            address="vault.example.com",
            port=8200,
            ssl_verify="true",
            client_cert=str(client_cert),
            client_key=str(client_key),
            ca_cert=None,
        )

        with pytest.raises(SystemExit):
            with caplog.at_level(logging.ERROR):
                self.command.main(args)
        assert messages.VAULT_CA_CERT_REQUIRED in caplog.text

    def test_set_vault_ssl_err(
        self, tmp_path, test_cert_content, test_key_content, caplog
    ):
        """Test setting vault configuration with SSL error."""
        url = get_server_location() + vault.VAULT_URI
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }

        # Create test certificate files
        client_cert = tmp_path / "client.pem"
        client_key = tmp_path / "client-key.pem"
        ca_cert = tmp_path / "ca.pem"

        client_cert.write_bytes(test_cert_content)
        client_key.write_bytes(test_key_content)
        ca_cert.write_bytes(test_cert_content)

        with requests_mock.Mocker() as mocker:
            mocker.post(url, exc=requests.exceptions.SSLError)
            args = Namespace(
                address="vault.example.com",
                port=8200,
                ssl_verify="true",
                client_cert=str(client_cert),
                client_key=str(client_key),
                ca_cert=str(ca_cert),
            )
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert expected_error in caplog.text

    def test_set_vault_conn_err(self, tmp_path, test_cert_content, caplog):
        """Test setting vault configuration with connection error."""
        url = get_server_location() + vault.VAULT_URI
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }

        # Create test certificate files
        client_cert = tmp_path / "client.pem"
        client_key = tmp_path / "client-key.pem"
        ca_cert = tmp_path / "ca.pem"

        client_cert.write_bytes(test_cert_content)
        client_key.write_bytes(test_cert_content)
        ca_cert.write_bytes(test_cert_content)

        with requests_mock.Mocker() as mocker:
            mocker.post(url, exc=requests.exceptions.ConnectTimeout)
            args = Namespace(
                address="vault.example.com",
                port=8200,
                ssl_verify="true",
                client_cert=str(client_cert),
                client_key=str(client_key),
                ca_cert=str(ca_cert),
            )
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert expected_error in caplog.text

    def test_set_vault_internal_err(
        self, tmp_path, test_cert_content, test_key_content, caplog
    ):
        """Test setting vault configuration with internal server error."""
        url = get_server_location() + vault.VAULT_URI
        error_message = "Server Error"

        # Create test certificate files
        client_cert = tmp_path / "client.pem"
        client_key = tmp_path / "client-key.pem"
        ca_cert = tmp_path / "ca.pem"

        client_cert.write_bytes(test_cert_content)
        client_key.write_bytes(test_cert_content)
        ca_cert.write_bytes(test_cert_content)

        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=500, json={"error": [error_message]})
            args = Namespace(
                address="vault.example.com",
                port=8200,
                ssl_verify="true",
                client_cert=str(client_cert),
                client_key=str(client_key),
                ca_cert=str(ca_cert),
            )
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert error_message in caplog.text

    def test_set_vault_bad_request(
        self, tmp_path, test_cert_content, test_key_content, caplog
    ):
        """Test setting vault configuration with bad request error."""
        url = get_server_location() + vault.VAULT_URI
        error_message = "Invalid address format"

        # Create test certificate files
        client_cert = tmp_path / "client.pem"
        client_key = tmp_path / "client-key.pem"
        ca_cert = tmp_path / "ca.pem"

        client_cert.write_bytes(test_cert_content)
        client_key.write_bytes(test_key_content)
        ca_cert.write_bytes(test_cert_content)

        with requests_mock.Mocker() as mocker:
            mocker.post(
                url,
                status_code=400,
                json={"address": [error_message]},
            )
            args = Namespace(
                address="vault.example.com",
                port=8200,
                ssl_verify="true",
                client_cert=str(client_cert),
                client_key=str(client_key),
                ca_cert=str(ca_cert),
            )
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert error_message in caplog.text

    def test_set_vault_file_not_found(self, tmp_path, caplog):
        """Test setting vault configuration with non-existent certificate file."""
        args = Namespace(
            address="vault.example.com",
            port=8200,
            ssl_verify="true",
            client_cert="/nonexistent/client.pem",
            client_key="/nonexistent/client-key.pem",
            ca_cert="/nonexistent/ca.pem",
        )

        with pytest.raises(SystemExit):
            with caplog.at_level(logging.ERROR):
                self.command.main(args)
        assert "does not exist" in caplog.text

    def test_set_vault_custom_port(
        self, tmp_path, test_cert_content, test_key_content, caplog
    ):
        """Test setting vault configuration with custom port."""
        url = get_server_location() + vault.VAULT_URI

        # Create test certificate files
        client_cert = tmp_path / "client.pem"
        client_key = tmp_path / "client-key.pem"
        ca_cert = tmp_path / "ca.pem"

        client_cert.write_bytes(test_cert_content)
        client_key.write_bytes(test_key_content)
        ca_cert.write_bytes(test_cert_content)

        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            args = Namespace(
                address="vault.example.com",
                port=9200,
                ssl_verify="true",
                client_cert=str(client_cert),
                client_key=str(client_key),
                ca_cert=str(ca_cert),
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.VAULT_CONFIG_SUCCESS in caplog.text
