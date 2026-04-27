"""Test vault credential edit in CLI."""

import sys
from unittest.mock import patch

import pytest

from qpc import messages
from qpc.cli import CLI
from qpc.cred import CREDENTIAL_URI
from qpc.utils import get_server_location


class TestVaultEditCredential:
    """Class for testing vault credential edit."""

    @patch("sys.stdin.isatty")
    def test_edit_vault_openshift_green_path(
        self,
        mock_isatty,
        caplog,
        requests_mock,
    ):
        """Test openshift cred edit with vault secret path."""
        caplog.set_level("INFO")
        mock_isatty.return_value = True
        url = get_server_location() + CREDENTIAL_URI
        # Mock the GET request to check if credential exists
        requests_mock.get(
            url,
            status_code=200,
            json={
                "count": 1,
                "results": [
                    {"id": 1, "name": "openshift_cred", "cred_type": "openshift"}
                ],
            },
        )
        # Mock the PATCH request to update the credential
        requests_mock.patch(url + "1/", status_code=200)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "openshift_cred",
            "--vault-secret-path",
            "secret/data/my-creds",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.CRED_UPDATED % "openshift_cred"

    @patch("sys.stdin.isatty")
    def test_edit_vault_ansible_green_path(
        self,
        mock_isatty,
        caplog,
        requests_mock,
    ):
        """Test ansible cred edit with vault secret path."""
        caplog.set_level("INFO")
        mock_isatty.return_value = True
        url = get_server_location() + CREDENTIAL_URI
        # Mock the GET request to check if credential exists
        requests_mock.get(
            url,
            status_code=200,
            json={
                "count": 1,
                "results": [{"id": 1, "name": "ansible_cred", "cred_type": "ansible"}],
            },
        )
        # Mock the PATCH request to update the credential
        requests_mock.patch(url + "1/", status_code=200)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "ansible_cred",
            "--vault-secret-path",
            "secret/data/my-creds",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.CRED_UPDATED % "ansible_cred"

        # Validate outgoing request payload
        payload = requests_mock.last_request.json()
        assert payload["vault_secret_path"] == "secret/data/my-creds"
        # Mount point should not be present when not provided
        assert "vault_mount_point" not in payload

    @patch("sys.stdin.isatty")
    def test_edit_vault_with_mount_point(
        self,
        mock_isatty,
        caplog,
        requests_mock,
    ):
        """Test openshift cred edit with vault secret path and mount point."""
        caplog.set_level("INFO")
        mock_isatty.return_value = True
        url = get_server_location() + CREDENTIAL_URI
        # Mock the GET request to check if credential exists
        requests_mock.get(
            url,
            status_code=200,
            json={
                "count": 1,
                "results": [
                    {"id": 1, "name": "openshift_cred", "cred_type": "openshift"}
                ],
            },
        )
        # Mock the PATCH request to update the credential
        requests_mock.patch(url + "1/", status_code=200)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "openshift_cred",
            "--vault-secret-path",
            "secret/data/my-creds",
            "--vault-mount-point",
            "custom-mount",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.CRED_UPDATED % "openshift_cred"

        # Validate outgoing request payload includes mount point when provided
        payload = requests_mock.last_request.json()
        assert payload["vault_secret_path"] == "secret/data/my-creds"
        assert payload["vault_mount_point"] == "custom-mount"

    def test_edit_vault_invalid_type(
        self,
        capsys,
        requests_mock,
    ):
        """Test vault secret path with invalid credential type."""
        url = get_server_location() + CREDENTIAL_URI
        # Mock the GET request to check if credential exists
        requests_mock.get(
            url,
            status_code=200,
            json={
                "count": 1,
                "results": [{"id": 1, "name": "network_cred", "cred_type": "network"}],
            },
        )
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "network_cred",
            "--vault-secret-path",
            "secret/data/my-creds",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert messages.CRED_VAULT_INVALID_TYPE in err

    def test_edit_vault_with_username(
        self,
        capsys,
        requests_mock,
    ):
        """Test that vault secret path with username fails."""
        url = get_server_location() + CREDENTIAL_URI
        # Mock the GET request to check if credential exists
        requests_mock.get(
            url,
            status_code=200,
            json={
                "count": 1,
                "results": [
                    {"id": 1, "name": "openshift_cred", "cred_type": "openshift"}
                ],
            },
        )
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "openshift_cred",
            "--username",
            "admin",
            "--vault-secret-path",
            "secret/data/my-creds",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert messages.CRED_VAULT_EXCLUSIVE_WITH_CREDS in err

    def test_edit_vault_with_sshkeyfile_mutually_exclusive(
        self,
        capsys,
        requests_mock,
    ):
        """Test that vault secret path and sshkeyfile are mutually exclusive."""
        url = get_server_location() + CREDENTIAL_URI
        requests_mock.get(
            url,
            status_code=200,
            json={
                "count": 1,
                "results": [
                    {"id": 1, "name": "openshift_cred", "cred_type": "openshift"}
                ],
            },
        )
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "openshift_cred",
            "--sshkeyfile",
            "/path/to/key",
            "--vault-secret-path",
            "secret/data/my-creds",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert "not allowed with argument" in err

    def test_edit_vault_mount_without_path(
        self,
        capsys,
        requests_mock,
    ):
        """Test vault mount point without vault secret path fails."""
        url = get_server_location() + CREDENTIAL_URI
        # Mock the GET request to check if credential exists
        requests_mock.get(
            url,
            status_code=200,
            json={
                "count": 1,
                "results": [
                    {"id": 1, "name": "openshift_cred", "cred_type": "openshift"}
                ],
            },
        )
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "openshift_cred",
            "--vault-mount-point",
            "custom-mount",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert messages.CRED_VAULT_MOUNT_REQUIRES_PATH in err
