"""Test openshift cred add in CLI."""

import sys
from unittest.mock import patch

import pytest

from qpc import messages
from qpc.cli import CLI
from qpc.cred import CREDENTIAL_URI, OPENSHIFT_CRED_TYPE
from qpc.utils import get_server_location


class TestOpenShiftAddCredential:
    """Class for testing OpenShift add credential."""

    @patch("sys.stdin.isatty")
    @pytest.mark.parametrize(
        "status_code,err_log_message",
        [
            (401, "qpc server login"),
            (500, "An internal server error occurred."),
        ],
    )
    def test_add_returning_error(
        self,
        mock_isatty,
        capsys,
        requests_mock,
        openshift_token_input,
        status_code,
        err_log_message,
    ):
        """Test openshift cred add with several errors."""
        mock_isatty.return_value = True
        url = get_server_location() + CREDENTIAL_URI
        requests_mock.post(url, status_code=status_code)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--name",
            "openshift_credential",
            "--type",
            OPENSHIFT_CRED_TYPE,
            "--token",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert err_log_message in err

    def test_add_no_type(
        self,
        capsys,
        openshift_token_input,
    ):
        """Test openshift cred add no type."""
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--name",
            "openshift_credential",
            "--token",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert (
            "qpc cred add: error: the following arguments are required: --type" in err
        )

    def test_add_no_token(
        self,
        capsys,
    ):
        """Test openshift cred add no token."""
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--name",
            "openshift_credential",
            "--type",
            OPENSHIFT_CRED_TYPE,
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert (
            "one of the arguments --password --sshkeyfile"
            " --sshkey --token is required" in err
        )

    def test_add_no_name(
        self,
        capsys,
        openshift_token_input,
    ):
        """Test openshift cred add no name."""
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--type",
            OPENSHIFT_CRED_TYPE,
            "--token",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert "the following arguments are required: --name" in err

    @patch("sys.stdin.isatty")
    @pytest.mark.parametrize("cred_type", ["OPENSHIFT", "openshift", "OpenShiFt"])
    def test_add_green_path(
        self,
        mock_isatty,
        caplog,
        requests_mock,
        openshift_token_input,
        cred_type,
    ):
        """Test openshift cred add green path."""
        caplog.set_level("INFO")
        mock_isatty.return_value = True
        url = get_server_location() + CREDENTIAL_URI
        requests_mock.post(url, status_code=201)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "add",
            "--name",
            "openshift_credential",
            "--type",
            cred_type,
            "--token",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.CRED_ADDED % "openshift_credential"

    @patch("sys.stdin.isatty")
    def test_no_api_info_shown_with_verbose_flag(
        self, mock_isatty, caplog, requests_mock, openshift_token_input
    ):
        """Test that no API information is shown when the -v flag is used."""
        caplog.set_level("INFO")
        mock_isatty.return_value = True
        url = get_server_location() + CREDENTIAL_URI
        requests_mock.post(url, status_code=201)
        sys.argv = [
            "/bin/qpc",
            "-v",
            "cred",
            "add",
            "--name",
            "openshift_credential",
            "--type",
            "openshift",
            "--token",
        ]
        CLI().main()
        for message in caplog.messages:
            assert "POST" not in message
