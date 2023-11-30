"""Test the CLI module."""

import logging
import sys
from argparse import ArgumentParser, Namespace
from unittest.mock import patch

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.cli import CLI
from qpc.cred import (
    CREDENTIAL_URI,
    NETWORK_CRED_TYPE,
    SATELLITE_CRED_TYPE,
    VCENTER_CRED_TYPE,
)
from qpc.cred.add import CredAddCommand
from qpc.utils import get_server_location


@pytest.fixture
def ssh_key(tmp_path):
    """Return the path to a fake ssh keyfile."""
    sshkey = tmp_path / "ssh_key"
    sshkey.write_text("fake ssh keyfile.")
    return str(sshkey)


@pytest.mark.usefixtures("server_config")
class TestCredentialAddCli:
    """Class for testing the credential add commands for qpc."""

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = CredAddCommand(subparser)

    def test_add_req_args_err(self):
        """Testing the add credential command required flags."""
        args = ["/bin/qpc", "credential", "add", "--name", "credential1"]
        with pytest.raises(SystemExit), patch.object(sys, "argv", args):
            CLI().main()

    def test_add_no_type(self):
        """Testing the add credential without type flag."""
        args = [
            "/bin/qpc",
            "credential",
            "add",
            "--name",
            "credential1",
            "--username",
            "foo",
            "--password",
        ]
        with pytest.raises(SystemExit), patch.object(sys, "argv", args):
            CLI().main()

    def test_add_bad_keyfile(self):
        """Testing the add credential command.

        When providing an invalid path for the sshkeyfile.
        """
        args = [
            "/bin/qpc",
            "credential",
            "add",
            "--name",
            "credential1",
            "--username",
            "root",
            "--sshkeyfile",
            "bad_path",
        ]
        with pytest.raises(SystemExit), patch.object(sys, "argv", args):
            CLI().main()

    def test_add_cred_name_dup(self, ssh_key):
        """Testing the add credential command duplicate name."""
        url = get_server_location() + CREDENTIAL_URI
        error = {"name": ["credential with this name already exists."]}
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=400, json=error)
            args = Namespace(
                name="cred_dup",
                username="root",
                type=NETWORK_CRED_TYPE,
                filename=ssh_key,
                password=None,
                become_password=None,
                ssh_passphrase=None,
            )
            with pytest.raises(SystemExit):
                self.command.main(args)

    def test_add_cred_ssl_err(self, ssh_key):
        """Testing the add credential command with a connection error."""
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, exc=requests.exceptions.SSLError)
            args = Namespace(
                name="credential1",
                username="root",
                type=NETWORK_CRED_TYPE,
                filename=ssh_key,
                password=None,
                become_password=None,
                ssh_passphrase=None,
            )
            with pytest.raises(SystemExit):
                self.command.main(args)

    def test_add_cred_conn_err(self, ssh_key):
        """Testing the add credential command with a connection error."""
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, exc=requests.exceptions.ConnectTimeout)
            args = Namespace(
                name="credential1",
                username="root",
                type=NETWORK_CRED_TYPE,
                filename=ssh_key,
                password=None,
                become_password=None,
                ssh_passphrase=None,
            )
            with pytest.raises(SystemExit):
                self.command.main(args)

    def test_add_host_cred(self, caplog, ssh_key):
        """Testing the add host cred command successfully."""
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            args = Namespace(
                name="credential1",
                username="root",
                type=NETWORK_CRED_TYPE,
                filename=ssh_key,
                password=None,
                ssh_passphrase=None,
                become_method=None,
                become_user=None,
                become_password=None,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.CRED_ADDED % "credential1"
                assert expected_message in caplog.text

    @patch("sys.stdin.isatty")
    @patch("qpc.cred.utils.get_multiline_pass")
    def test_add_host_cred_with_sshkey(self, mock_multiline_pass, mock_isatty, caplog):
        """Testing the add host cred command with an ssh_key successfully."""
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            args = Namespace(
                type=NETWORK_CRED_TYPE,
                name="credential1",
                username="root",
                password=None,
                filename=None,
                ssh_key=True,
                ssh_passphrase=None,
            )
            mock_isatty.return_value = True
            mock_multiline_pass.return_value = "This\nIs\nA\nMulti-Line\nOpenSSH Key\n"
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.CRED_ADDED % "credential1"
                assert expected_message in caplog.text

    @patch("sys.stdin.isatty")
    @patch("sys.stdin.readlines")
    def test_add_host_cred_with_sshkey_from_stdin(
        self, mock_readlines, mock_isatty, caplog
    ):
        """Testing the add host cred command with an ssh_key from stdin successfully."""
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            args = Namespace(
                type=NETWORK_CRED_TYPE,
                name="credential1",
                username="root",
                password=None,
                filename=None,
                ssh_key=True,
                ssh_passphrase=None,
            )
            mock_isatty.return_value = False
            mock_readlines.return_value = "Multi-Line\nOpenSSH Key\nFrom Stdin\n"
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.CRED_ADDED % "credential1"
                assert expected_message in caplog.text

    @patch("sys.stdin.isatty")
    @patch("getpass._raw_input")
    @patch("qpc.cred.utils.get_multiline_pass")
    def test_add_host_cred_with_sshkey_and_passphrase(
        self, mock_multiline_pass, mock_raw_input, mock_isatty, caplog
    ):
        """Testing add host cred with an ssh_key and ssh_passphrase successfully."""
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            args = Namespace(
                type=NETWORK_CRED_TYPE,
                name="credential1",
                username="root",
                password=None,
                filename=None,
                ssh_key=True,
                ssh_passphrase=True,
            )
            mock_isatty.return_value = True
            mock_multiline_pass.return_value = "OpenSSH Key\nWith passphrase\n"
            mock_raw_input.return_value = "This is the passphrase"
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.CRED_ADDED % "credential1"
                assert expected_message in caplog.text

    def test_add_host_cred_with_become(self, caplog, ssh_key):
        """Testing the add host cred command successfully."""
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            args = Namespace(
                name="credential1",
                username="root",
                type=NETWORK_CRED_TYPE,
                filename=ssh_key,
                password=None,
                ssh_passphrase=None,
                become_method="sudo",
                become_user="root",
                become_password=None,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.CRED_ADDED % "credential1"
                assert expected_message in caplog.text

    @patch("sys.stdin.isatty")
    @patch("getpass._raw_input")
    def test_add_vcenter_cred(self, do_mock_raw_input, mock_isatty, caplog):
        """Testing the add vcenter cred command successfully."""
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            args = Namespace(
                name="credential1",
                type=VCENTER_CRED_TYPE,
                username="root",
                password="sdf",
            )
            mock_isatty.return_value = True
            do_mock_raw_input.return_value = "abc"
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.CRED_ADDED % "credential1"
                assert expected_message in caplog.text

    @patch("sys.stdin.isatty")
    @patch("getpass._raw_input")
    def test_add_sat_cred(self, do_mock_raw_input, mock_isatty, caplog):
        """Testing the add sat cred command successfully."""
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=201)
            args = Namespace(
                name="credential1",
                type=SATELLITE_CRED_TYPE,
                username="root",
                password="sdf",
            )
            mock_isatty.return_value = True
            do_mock_raw_input.return_value = "abc"
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.CRED_ADDED % "credential1"
                assert expected_message in caplog.text

    @patch("sys.stdin.isatty")
    @patch("getpass._raw_input")
    def test_add_cred_401(self, do_mock_raw_input, mock_isatty):
        """Testing the 401 error flow."""
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=401)
            args = Namespace(
                name="credential1",
                type=SATELLITE_CRED_TYPE,
                username="root",
                password="sdf",
            )
            mock_isatty.return_value = True
            do_mock_raw_input.return_value = "abc"
            with pytest.raises(SystemExit):
                self.command.main(args)

    @patch("getpass._raw_input")
    def test_add_cred_expired(self, do_mock_raw_input):
        """Testing the token expired flow."""
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            expired = {"detail": "Token has expired"}
            mocker.post(url, status_code=400, json=expired)
            args = Namespace(
                name="credential1",
                type=SATELLITE_CRED_TYPE,
                username="root",
                password="sdf",
            )
            do_mock_raw_input.return_value = "abc"
            with pytest.raises(SystemExit):
                self.command.main(args)
