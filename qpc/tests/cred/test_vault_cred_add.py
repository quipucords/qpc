"""Test vault credential add in CLI."""

import sys
from unittest.mock import patch

import pytest

from qpc import messages
from qpc.cli import CLI
from qpc.cred import CREDENTIAL_URI, OPENSHIFT_CRED_TYPE
from qpc.source import ANSIBLE_SOURCE_TYPE
from qpc.utils import get_server_location


class TestVaultAddCredential:
    """Class for testing vault credential add."""

    @patch("sys.stdin.isatty")
    def test_add_vault_openshift_green_path(
        self,
        mock_isatty,
        caplog,
        requests_mock,
    ):
        """Test openshift cred add with vault secret path."""
        caplog.set_level("INFO")
        mock_isatty.return_value = True
        url = get_server_location() + CREDENTIAL_URI
        requests_mock.post(url, status_code=201)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--name",
            "openshift_vault_credential",
            "--type",
            OPENSHIFT_CRED_TYPE,
            "--vault-secret-path",
            "secret/data/my-creds",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.CRED_ADDED % "openshift_vault_credential"

    @patch("sys.stdin.isatty")
    def test_add_vault_ansible_green_path(
        self,
        mock_isatty,
        caplog,
        requests_mock,
    ):
        """Test ansible cred add with vault secret path."""
        caplog.set_level("INFO")
        mock_isatty.return_value = True
        url = get_server_location() + CREDENTIAL_URI
        requests_mock.post(url, status_code=201)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--name",
            "ansible_vault_credential",
            "--type",
            ANSIBLE_SOURCE_TYPE,
            "--vault-secret-path",
            "secret/data/my-creds",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.CRED_ADDED % "ansible_vault_credential"

        # Validate outgoing request payload
        payload = requests_mock.last_request.json()
        assert payload["vault_secret_path"] == "secret/data/my-creds"
        # Mount point should not be present when not provided
        assert "vault_mount_point" not in payload

    @patch("sys.stdin.isatty")
    def test_add_vault_with_mount_point(
        self,
        mock_isatty,
        caplog,
        requests_mock,
    ):
        """Test openshift cred add with vault secret path and mount point."""
        caplog.set_level("INFO")
        mock_isatty.return_value = True
        url = get_server_location() + CREDENTIAL_URI
        requests_mock.post(url, status_code=201)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--name",
            "openshift_vault_credential",
            "--type",
            OPENSHIFT_CRED_TYPE,
            "--vault-secret-path",
            "secret/data/my-creds",
            "--vault-mount-point",
            "custom-mount",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.CRED_ADDED % "openshift_vault_credential"

        # Validate outgoing request payload includes mount point when provided
        payload = requests_mock.last_request.json()
        assert payload["vault_secret_path"] == "secret/data/my-creds"
        assert payload["vault_mount_point"] == "custom-mount"

    def test_add_vault_invalid_type(
        self,
        capsys,
    ):
        """Test vault secret path with invalid credential type."""
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--name",
            "network_vault_credential",
            "--type",
            "network",
            "--vault-secret-path",
            "secret/data/my-creds",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert messages.CRED_VAULT_INVALID_TYPE in err

    @patch("sys.stdin.isatty")
    def test_add_vault_with_username(
        self,
        mock_isatty,
        capsys,
        requests_mock,
    ):
        """Test that vault secret path with username fails."""
        mock_isatty.return_value = True
        url = get_server_location() + CREDENTIAL_URI
        requests_mock.post(url, status_code=201)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--name",
            "openshift_vault_credential",
            "--type",
            OPENSHIFT_CRED_TYPE,
            "--username",
            "admin",
            "--vault-secret-path",
            "secret/data/my-creds",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert messages.CRED_VAULT_EXCLUSIVE_WITH_CREDS in err

    @patch("sys.stdin.isatty")
    def test_add_vault_mount_without_path(
        self,
        mock_isatty,
        capsys,
        requests_mock,
        openshift_token_input,
    ):
        """Test that vault mount point without vault secret path fails."""
        mock_isatty.return_value = True
        url = get_server_location() + CREDENTIAL_URI
        requests_mock.post(url, status_code=201)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--name",
            "openshift_vault_credential",
            "--type",
            OPENSHIFT_CRED_TYPE,
            "--token",
            "--vault-mount-point",
            "custom-mount",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert messages.CRED_VAULT_MOUNT_REQUIRES_PATH in err

    @patch("sys.stdin.isatty")
    def test_add_vault_with_sshkeyfile_mutually_exclusive(
        self,
        mock_isatty,
        capsys,
    ):
        """Test that vault secret path and sshkeyfile are mutually exclusive."""
        mock_isatty.return_value = True
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--name",
            "openshift_vault_credential",
            "--type",
            OPENSHIFT_CRED_TYPE,
            "--sshkeyfile",
            "/path/to/key",
            "--vault-secret-path",
            "secret/data/my-creds",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert "not allowed with argument" in err

    @patch("sys.stdin.isatty")
    def test_add_vault_with_token_mutually_exclusive(
        self,
        mock_isatty,
        capsys,
    ):
        """Test that vault secret path and token are mutually exclusive."""
        mock_isatty.return_value = True
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--name",
            "openshift_vault_credential",
            "--type",
            OPENSHIFT_CRED_TYPE,
            "--token",
            "--vault-secret-path",
            "secret/data/my-creds",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert "not allowed with argument" in err
