"""Test the vault utils module."""

import base64
import logging
from argparse import ArgumentParser
from pathlib import Path
from unittest.mock import patch

import pytest

from qpc.vault.utils import (
    CERT_TYPE_CA,
    CERT_TYPE_CLIENT_CERT,
    CERT_TYPE_CLIENT_KEY,
    add_vault_arguments,
    read_and_encode_cert_file,
    str_to_bool,
)


@pytest.mark.usefixtures("server_config")
class TestVaultUtils:
    """Class for testing vault utility functions."""

    def test_str_to_bool_true(self):
        """Test str_to_bool with 'true' string."""
        assert str_to_bool("true") is True

    def test_str_to_bool_false(self):
        """Test str_to_bool with 'false' string."""
        assert str_to_bool("false") is False

    def test_str_to_bool_other(self):
        """Test str_to_bool with other string values."""
        assert str_to_bool("True") is False
        assert str_to_bool("False") is False
        assert str_to_bool("yes") is False
        assert str_to_bool("") is False

    def test_read_and_encode_cert_file_success(self, tmp_path, test_cert_content):
        """Test successful reading and encoding of certificate file."""
        cert_file = tmp_path / "test.pem"
        cert_file.write_bytes(test_cert_content)

        result = read_and_encode_cert_file(str(cert_file), CERT_TYPE_CLIENT_CERT)
        expected = base64.b64encode(test_cert_content).decode("utf-8")
        assert result == expected

    def test_read_and_encode_cert_file_not_found(self, caplog):
        """Test reading certificate file that doesn't exist."""
        with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
            read_and_encode_cert_file("/nonexistent/file.pem", CERT_TYPE_CA)
        assert "does not exist" in caplog.text

    def test_read_and_encode_cert_file_permission_denied(
        self, tmp_path, test_cert_content, caplog
    ):
        """Test reading certificate file with permission denied."""
        cert_file = tmp_path / "noperm.pem"
        cert_file.write_bytes(test_cert_content)

        with patch.object(Path, "read_bytes") as mock_read:
            mock_read.side_effect = PermissionError("Permission denied")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                read_and_encode_cert_file(str(cert_file), CERT_TYPE_CLIENT_KEY)
            assert "Permission denied" in caplog.text

    def test_read_and_encode_cert_file_os_error(
        self, tmp_path, test_cert_content, caplog
    ):
        """Test reading certificate file with OS error."""
        cert_file = tmp_path / "error.pem"
        cert_file.write_bytes(test_cert_content)

        with patch.object(Path, "read_bytes") as mock_read:
            mock_read.side_effect = OSError("OS error occurred")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                read_and_encode_cert_file(str(cert_file), CERT_TYPE_CA)
            assert "Failed to read" in caplog.text
            assert "OS error occurred" in caplog.text

    def test_read_and_encode_cert_file_unicode_decode_error(
        self, tmp_path, test_cert_content, caplog
    ):
        """Test reading certificate file with unicode decode error."""
        cert_file = tmp_path / "unicode.pem"
        cert_file.write_bytes(test_cert_content)

        with patch.object(Path, "read_bytes") as mock_read:
            mock_read.side_effect = UnicodeDecodeError(
                "utf-8", b"", 0, 1, "invalid start byte"
            )
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                read_and_encode_cert_file(str(cert_file), CERT_TYPE_CLIENT_CERT)
            assert "Failed to read" in caplog.text

    def test_add_vault_arguments_required_certs_true_required_address_true(self):
        """Test adding vault arguments with required certs and required address."""
        parser = ArgumentParser()
        add_vault_arguments(parser, required_certs=True, required_address=True)

        # Check that arguments were added
        args = parser.parse_args(
            [
                "--address",
                "vault.example.com",
                "--port",
                "8200",
                "--ssl-verify",
                "true",
                "--client-cert",
                "client.pem",
                "--client-key",
                "client-key.pem",
                "--ca-cert",
                "ca.pem",
            ]
        )

        assert args.address == "vault.example.com"
        assert args.port == 8200
        assert args.ssl_verify == "true"
        assert args.client_cert == "client.pem"
        assert args.client_key == "client-key.pem"
        assert args.ca_cert == "ca.pem"

    def test_add_vault_arguments_required_certs_false_required_address_false(self):
        """Test adding vault arguments with optional certs and optional address."""
        parser = ArgumentParser()
        add_vault_arguments(parser, required_certs=False, required_address=False)

        # Check that arguments can be omitted
        args = parser.parse_args([])

        assert args.address is None
        assert args.port == 8200  # default
        assert args.ssl_verify is None
        assert args.client_cert is None
        assert args.client_key is None
        assert args.ca_cert is None

    def test_add_vault_arguments_defaults(self):
        """Test default values for vault arguments."""
        parser = ArgumentParser()
        add_vault_arguments(parser, required_certs=True, required_address=True)

        args = parser.parse_args(
            [
                "--address",
                "vault.example.com",
                "--client-cert",
                "client.pem",
                "--client-key",
                "client-key.pem",
            ]
        )

        assert args.port == 8200  # default port
        assert args.ssl_verify == "true"  # default when required_certs=True

    def test_add_vault_arguments_ssl_verify_false(self):
        """Test ssl_verify argument with false value."""
        parser = ArgumentParser()
        add_vault_arguments(parser, required_certs=True, required_address=True)

        args = parser.parse_args(
            [
                "--address",
                "vault.example.com",
                "--ssl-verify",
                "false",
                "--client-cert",
                "client.pem",
                "--client-key",
                "client-key.pem",
            ]
        )

        assert args.ssl_verify == "false"

    def test_add_vault_arguments_ssl_verify_case_insensitive(self):
        """Test ssl_verify argument is case insensitive."""
        parser = ArgumentParser()
        add_vault_arguments(parser, required_certs=True, required_address=True)

        args = parser.parse_args(
            [
                "--address",
                "vault.example.com",
                "--ssl-verify",
                "TRUE",
                "--client-cert",
                "client.pem",
                "--client-key",
                "client-key.pem",
            ]
        )

        assert args.ssl_verify == "true"
