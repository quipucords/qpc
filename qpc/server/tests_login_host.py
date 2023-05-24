"""Test the CLI module."""

import sys
import unittest
from argparse import ArgumentParser, Namespace  # noqa: I100
from io import StringIO
from unittest.mock import patch

import requests_mock

from qpc import messages
from qpc.server import LOGIN_URI
from qpc.server.login_host import LoginHostCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

TMP_KEY = "/tmp/testkey"


class LoginCliTests(unittest.TestCase):
    """Class for testing the login server command for qpc."""

    @classmethod
    def setUpClass(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = LoginHostCommand(subparser)

    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()
        self.login_url = get_server_location() + LOGIN_URI
        self.success_json = {"token": "a_token"}

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    @patch("getpass._raw_input")
    def test_login_bad_cred(self, do_mock_raw_input):
        """Testing the login with bad creds."""
        server_out = StringIO()
        e_msg = "Unable to log in with provided credentials."
        error = {"detail": [e_msg]}
        with requests_mock.Mocker() as mocker, patch.object(
            self.command, "password", "password"
        ):
            mocker.post(self.login_url, status_code=400, json=error)
            args = Namespace(username="admin")
            do_mock_raw_input.return_value = "abc"
            with self.assertRaises(SystemExit):
                with redirect_stdout(server_out):
                    self.command.main(args)
                    self.assertTrue(e_msg in server_out.getvalue())

    @patch("getpass._raw_input")
    def test_login_good(self, do_mock_raw_input):
        """Testing the login with good creds."""
        with requests_mock.Mocker() as mocker, patch.object(
            self.command, "password", "password"
        ):
            mocker.post(self.login_url, status_code=200, json=self.success_json)
            args = Namespace(username="admin")
            do_mock_raw_input.return_value = "abc"
            with self.assertLogs(level="INFO") as log:
                self.command.main(args)
                self.assertIn(messages.LOGIN_SUCCESS, log.output[-1])

    @patch("builtins.input")
    @patch("getpass._raw_input")
    def test_prompts_with_no_args(self, user_mock, pass_mock):
        """Testing the login with no args passed."""
        pass_mock.return_value = "abc"
        user_mock.return_value = "admin"
        with requests_mock.Mocker() as mocker:
            mocker.post(self.login_url, status_code=200, json=self.success_json)

            args = Namespace()
            with self.assertLogs(level="INFO") as log:
                self.command.main(args)
                self.assertIn(messages.LOGIN_SUCCESS, log.output[-1])

    def test_no_prompts_with_args(self):
        """Testing no prompts with args passed."""
        with requests_mock.Mocker() as mocker:
            mocker.post(self.login_url, status_code=200, json=self.success_json)

            args = Namespace(username="admin", password="pass")
            with self.assertLogs(level="INFO") as log:
                self.command.main(args)
                self.assertIn(messages.LOGIN_SUCCESS, log.output[-1])
