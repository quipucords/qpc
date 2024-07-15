"""Test the CLI module."""

import logging
import sys
from argparse import ArgumentParser, Namespace  # noqa: I100
from io import StringIO
from unittest.mock import patch

import pytest
import requests_mock

from qpc import messages
from qpc.server import LOGIN_URI
from qpc.server.login_host import LoginHostCommand
from qpc.tests.utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

TMP_KEY = "/tmp/testkey"


class TestLoginCli:
    """Class for testing the login server command for qpc."""

    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = LoginHostCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()
        self.login_url = get_server_location() + LOGIN_URI
        self.success_json = {"token": "a_token"}

    def teardown_method(self, _test_method):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    @patch("getpass._raw_input")
    def test_login_bad_cred(self, do_mock_raw_input):
        """Testing the login with bad creds."""
        server_out = StringIO()
        e_msg = "Unable to log in with provided credentials."
        error = {"detail": [e_msg]}
        with (
            requests_mock.Mocker() as mocker,
            patch.object(self.command, "password", "password"),
        ):
            mocker.post(self.login_url, status_code=400, json=error)
            args = Namespace(username="admin")
            do_mock_raw_input.return_value = "abc"
            with pytest.raises(SystemExit):
                with redirect_stdout(server_out):
                    self.command.main(args)
                    assert e_msg in server_out.getvalue()

    @patch("getpass._raw_input")
    def test_login_good(self, do_mock_raw_input, caplog):
        """Testing the login with good creds."""
        with (
            requests_mock.Mocker() as mocker,
            patch.object(self.command, "password", "password"),
        ):
            mocker.post(self.login_url, status_code=200, json=self.success_json)
            args = Namespace(username="admin")
            do_mock_raw_input.return_value = "abc"
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.LOGIN_SUCCESS in caplog.text

    @patch("builtins.input")
    @patch("getpass._raw_input")
    def test_prompts_with_no_args(self, user_mock, pass_mock, caplog):
        """Testing the login with no args passed."""
        pass_mock.return_value = "abc"
        user_mock.return_value = "admin"
        with requests_mock.Mocker() as mocker:
            mocker.post(self.login_url, status_code=200, json=self.success_json)

            args = Namespace()
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.LOGIN_SUCCESS in caplog.text

    def test_no_prompts_with_args(self, caplog):
        """Testing no prompts with args passed."""
        with requests_mock.Mocker() as mocker:
            mocker.post(self.login_url, status_code=200, json=self.success_json)

            args = Namespace(username="admin", password="pass")
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.LOGIN_SUCCESS in caplog.text
