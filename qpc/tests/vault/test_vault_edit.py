"""Test the "vault edit" command."""

import logging
from argparse import ArgumentParser, Namespace

import pytest
import requests
import requests_mock

from qpc import messages, vault
from qpc.request import CONNECTION_ERROR_MSG
from qpc.tests.utilities import DEFAULT_CONFIG
from qpc.utils import get_server_location, write_server_config
from qpc.vault.edit import VaultEditCommand


@pytest.mark.usefixtures("server_config")
class TestVaultEditCli:
    """Class for testing the vault edit command for qpc."""

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = VaultEditCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)

    def test_edit_vault_address_only(self, caplog):
        """Test editing vault configuration with address only."""
        url = get_server_location() + vault.VAULT_URI

        with requests_mock.Mocker() as mocker:
            mocker.patch(url, status_code=200)
            args = Namespace(
                address="new-vault.example.com",
                port=None,
                ssl_verify=None,
                client_cert=None,
                client_key=None,
                ca_cert=None,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.VAULT_UPDATED in caplog.text

    def test_edit_vault_port_only(self, caplog):
        """Test editing vault configuration with port only."""
        url = get_server_location() + vault.VAULT_URI

        with requests_mock.Mocker() as mocker:
            mocker.patch(url, status_code=200)
            args = Namespace(
                address=None,
                port=9200,
                ssl_verify=None,
                client_cert=None,
                client_key=None,
                ca_cert=None,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.VAULT_UPDATED in caplog.text

    def test_edit_vault_ssl_verify_only(self, caplog):
        """Test editing vault configuration with ssl_verify only."""
        url = get_server_location() + vault.VAULT_URI

        with requests_mock.Mocker() as mocker:
            mocker.patch(url, status_code=200)
            args = Namespace(
                address=None,
                port=None,
                ssl_verify="false",
                client_cert=None,
                client_key=None,
                ca_cert=None,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.VAULT_UPDATED in caplog.text

    def test_edit_vault_ca_cert_only(self, tmp_path, caplog):
        """Test editing vault configuration with CA cert only."""
        url = get_server_location() + vault.VAULT_URI

        ca_cert = tmp_path / "ca.pem"
        ca_cert.write_bytes(b"test ca cert")

        with requests_mock.Mocker() as mocker:
            mocker.patch(url, status_code=200)
            args = Namespace(
                address=None,
                port=None,
                ssl_verify=None,
                client_cert=None,
                client_key=None,
                ca_cert=str(ca_cert),
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.VAULT_UPDATED in caplog.text

    def test_edit_vault_client_certs(self, tmp_path, caplog):
        """Test editing vault configuration with client cert and key."""
        url = get_server_location() + vault.VAULT_URI

        client_cert = tmp_path / "client.pem"
        client_key = tmp_path / "client-key.pem"

        client_cert.write_bytes(b"test client cert")
        client_key.write_bytes(b"test client key")

        with requests_mock.Mocker() as mocker:
            mocker.patch(url, status_code=200)
            args = Namespace(
                address=None,
                port=None,
                ssl_verify=None,
                client_cert=str(client_cert),
                client_key=str(client_key),
                ca_cert=None,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.VAULT_UPDATED in caplog.text

    def test_edit_vault_multiple_fields(self, tmp_path, caplog):
        """Test editing vault configuration with multiple fields."""
        url = get_server_location() + vault.VAULT_URI

        ca_cert = tmp_path / "ca.pem"
        ca_cert.write_bytes(b"test ca cert")

        with requests_mock.Mocker() as mocker:
            mocker.patch(url, status_code=200)
            args = Namespace(
                address="new-vault.example.com",
                port=9200,
                ssl_verify="true",
                client_cert=None,
                client_key=None,
                ca_cert=str(ca_cert),
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.VAULT_UPDATED in caplog.text

    def test_edit_vault_no_args(self, caplog):
        """Test editing vault configuration with no arguments fails."""
        args = Namespace(
            address=None,
            port=None,
            ssl_verify=None,
            client_cert=None,
            client_key=None,
            ca_cert=None,
        )

        with pytest.raises(SystemExit):
            with caplog.at_level(logging.ERROR):
                self.command.main(args)
        assert messages.VAULT_EDIT_NO_ARGS in caplog.text

    def test_edit_vault_client_cert_without_key(self, tmp_path, caplog):
        """Test editing vault with client cert but no key fails."""
        client_cert = tmp_path / "client.pem"
        client_cert.write_bytes(b"test client cert")

        args = Namespace(
            address=None,
            port=None,
            ssl_verify=None,
            client_cert=str(client_cert),
            client_key=None,
            ca_cert=None,
        )

        with pytest.raises(SystemExit):
            with caplog.at_level(logging.ERROR):
                self.command.main(args)
        assert messages.VAULT_CLIENT_CERT_KEY_MISMATCH in caplog.text

    def test_edit_vault_client_key_without_cert(self, tmp_path, caplog):
        """Test editing vault with client key but no cert fails."""
        client_key = tmp_path / "client-key.pem"
        client_key.write_bytes(b"test client key")

        args = Namespace(
            address=None,
            port=None,
            ssl_verify=None,
            client_cert=None,
            client_key=str(client_key),
            ca_cert=None,
        )

        with pytest.raises(SystemExit):
            with caplog.at_level(logging.ERROR):
                self.command.main(args)
        assert messages.VAULT_CLIENT_CERT_KEY_MISMATCH in caplog.text

    def test_edit_vault_ssl_err(self, caplog):
        """Test editing vault configuration with SSL error."""
        url = get_server_location() + vault.VAULT_URI
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }

        with requests_mock.Mocker() as mocker:
            mocker.patch(url, exc=requests.exceptions.SSLError)
            args = Namespace(
                address="vault.example.com",
                port=None,
                ssl_verify=None,
                client_cert=None,
                client_key=None,
                ca_cert=None,
            )
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert expected_error in caplog.text

    def test_edit_vault_conn_err(self, caplog):
        """Test editing vault configuration with connection error."""
        url = get_server_location() + vault.VAULT_URI
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }

        with requests_mock.Mocker() as mocker:
            mocker.patch(url, exc=requests.exceptions.ConnectTimeout)
            args = Namespace(
                address="vault.example.com",
                port=None,
                ssl_verify=None,
                client_cert=None,
                client_key=None,
                ca_cert=None,
            )
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert expected_error in caplog.text

    def test_edit_vault_internal_err(self, caplog):
        """Test editing vault configuration with internal server error."""
        url = get_server_location() + vault.VAULT_URI
        error_message = "Server Error"

        with requests_mock.Mocker() as mocker:
            mocker.patch(url, status_code=500, json={"error": ["Server Error"]})
            args = Namespace(
                address="vault.example.com",
                port=None,
                ssl_verify=None,
                client_cert=None,
                client_key=None,
                ca_cert=None,
            )
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert error_message in caplog.text

    def test_edit_vault_not_found(self, caplog):
        """Test editing vault configuration that doesn't exist."""
        url = get_server_location() + vault.VAULT_URI

        with requests_mock.Mocker() as mocker:
            mocker.patch(
                url,
                status_code=404,
                json={"detail": "Not found."},
            )
            args = Namespace(
                address="vault.example.com",
                port=None,
                ssl_verify=None,
                client_cert=None,
                client_key=None,
                ca_cert=None,
            )
            with pytest.raises(SystemExit):
                with caplog.at_level(logging.ERROR):
                    self.command.main(args)
            assert "Not found" in caplog.text

    def test_edit_vault_all_fields(self, tmp_path, caplog):
        """Test editing vault configuration with all fields."""
        url = get_server_location() + vault.VAULT_URI

        client_cert = tmp_path / "client.pem"
        client_key = tmp_path / "client-key.pem"
        ca_cert = tmp_path / "ca.pem"

        client_cert.write_bytes(b"test client cert")
        client_key.write_bytes(b"test client key")
        ca_cert.write_bytes(b"test ca cert")

        with requests_mock.Mocker() as mocker:
            mocker.patch(url, status_code=200)
            args = Namespace(
                address="new-vault.example.com",
                port=9200,
                ssl_verify="false",
                client_cert=str(client_cert),
                client_key=str(client_key),
                ca_cert=str(ca_cert),
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.VAULT_UPDATED in caplog.text
