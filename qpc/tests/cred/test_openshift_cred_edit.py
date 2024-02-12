"""Test openshift cred edit in CLI."""

import sys
from unittest.mock import patch

import pytest

from qpc import messages
from qpc.cli import CLI
from qpc.cred import CREDENTIAL_URI, OPENSHIFT_CRED_TYPE, SATELLITE_CRED_TYPE
from qpc.utils import get_server_location


class TestOpenShiftEditCredential:
    """Class for testing OpenShift edit credential."""

    @patch("sys.stdin.isatty")
    def test_edit_partial_green_path(
        self,
        mock_isatty,
        caplog,
        requests_mock,
        openshift_token_input,
    ):
        """Test partial openshift edit cred successfully."""
        mock_isatty.return_value = True
        caplog.set_level("INFO")
        url_get = get_server_location() + CREDENTIAL_URI
        url_patch = get_server_location() + CREDENTIAL_URI + "1/"
        results = [
            {
                "id": 1,
                "name": "openshift_cred",
                "cred_type": OPENSHIFT_CRED_TYPE,
                "token": "********",
            }
        ]
        data = {"count": 1, "results": results}
        requests_mock.get(url_get, status_code=200, json=data)
        requests_mock.patch(url_patch, status_code=200)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "openshift_cred",
            "--token",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.CRED_UPDATED % "openshift_cred"

    @patch("sys.stdin.isatty")
    def test_edit_green_path(
        self,
        mock_isatty,
        caplog,
        requests_mock,
        openshift_token_input,
    ):
        """Test openshift edit cred successfully."""
        mock_isatty.return_value = True
        caplog.set_level("INFO")
        url_get = get_server_location() + CREDENTIAL_URI
        url_patch = get_server_location() + CREDENTIAL_URI + "1/"
        results = [
            {
                "id": 1,
                "name": "openshift_cred",
                "cred_type": OPENSHIFT_CRED_TYPE,
                "token": "********",
            }
        ]
        data = {"count": 1, "results": results}
        requests_mock.get(url_get, status_code=200, json=data)
        requests_mock.patch(url_patch, status_code=200)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "openshift_cred_2",
            "--token",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.CRED_UPDATED % "openshift_cred_2"

    @pytest.mark.parametrize(
        "status_code,err_log_message",
        [
            (401, "qpc server login"),
            (500, "An internal server error occurred."),
        ],
    )
    def test_edit_returning_error(
        self,
        capsys,
        requests_mock,
        openshift_token_input,
        status_code,
        err_log_message,
    ):
        """Test openshift edit cred w/ errors."""
        url_get = get_server_location() + CREDENTIAL_URI
        requests_mock.get(url_get, status_code=status_code, json=None)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "openshift_cred_2",
            "--token",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert err_log_message in err

    def test_edit_incorrect_arg(
        self,
        capsys,
        requests_mock,
    ):
        """Test openshift edit cred with incorrect args."""
        url_get = get_server_location() + CREDENTIAL_URI
        url_patch = get_server_location() + CREDENTIAL_URI + "1/"
        results = [
            {
                "id": 1,
                "name": "openshift_cred",
                "cred_type": OPENSHIFT_CRED_TYPE,
                "token": "********",
            }
        ]
        data = {"count": 1, "results": results}
        requests_mock.get(url_get, status_code=200, json=data)
        requests_mock.patch(url_patch, status_code=400)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "openshift_cred_2",
            "--password",
            "mock_password",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert "unrecognized argument" in err

    def test_edit_change_cred_type(
        self,
        capsys,
        requests_mock,
    ):
        """Test existing ocp credential cred type."""
        url_get = get_server_location() + CREDENTIAL_URI
        results = [
            {
                "id": 1,
                "name": "openshift_cred",
                "cred_type": OPENSHIFT_CRED_TYPE,
                "token": "********",
            }
        ]
        data = {"count": 1, "results": results}
        requests_mock.get(url_get, status_code=200, json=data)
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "openshift_cred",
            "--type",
            SATELLITE_CRED_TYPE,
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert "error: unrecognized arguments: --type satellite" in err

    def test_edit_with_token_and_password_as_args(
        self,
        capsys,
    ):
        """Test openshift cred edit with password and token args."""
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "openshift_cred",
            "--password",
            "--token",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert "argument --token: not allowed with argument --password" in err

    def test_edit_with_token_and_sshkeyfile_as_args(
        self,
        capsys,
    ):
        """Test openshift cred edit with token and sshkeyfile args."""
        sys.argv = [
            "/bin/qpc",
            "cred",
            "edit",
            "--name",
            "openshift_cred",
            "--sshkeyfile",
            "mock_path/test.pem",
            "--token",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert "argument --token: not allowed with argument --sshkeyfile" in err
