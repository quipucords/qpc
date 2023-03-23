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
PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest="subcommand")


class LoginCliTests(unittest.TestCase):
    """Class for testing the login server command for qpc."""

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
        with requests_mock.Mocker() as mocker:
            mocker.post(self.login_url, status_code=400, json=error)
            lhc = LoginHostCommand(SUBPARSER)
            lhc.password = "password"
            args = Namespace(username="admin")
            do_mock_raw_input.return_value = "abc"
            with self.assertRaises(SystemExit):
                with redirect_stdout(server_out):
                    lhc.main(args)
                    self.assertTrue(e_msg in server_out.getvalue())

    @patch("getpass._raw_input")
    def test_login_good(self, do_mock_raw_input):
        """Testing the login with good creds."""
        server_out = StringIO()
        with requests_mock.Mocker() as mocker:
            mocker.post(self.login_url, status_code=200, json=self.success_json)
            lhc = LoginHostCommand(SUBPARSER)
            lhc.password = "password"
            args = Namespace(username="admin")
            do_mock_raw_input.return_value = "abc"
            with redirect_stdout(server_out):
                lhc.main(args)
                result = server_out.getvalue().rstrip()
                self.assertEqual(result, messages.LOGIN_SUCCESS)

    @patch("builtins.input")
    @patch("getpass._raw_input")
    def test_prompts_with_no_args(self, user_mock, pass_mock):
        """Testing the login with no args passed."""
        server_out = StringIO()
        pass_mock.return_value = "abc"
        user_mock.return_value = "admin"
        with requests_mock.Mocker() as mocker:
            mocker.post(self.login_url, status_code=200, json=self.success_json)
            lhc = LoginHostCommand(SUBPARSER)
            args = Namespace()
            with redirect_stdout(server_out):
                lhc.main(args)
                result = server_out.getvalue().rstrip()
                self.assertEqual(result, messages.LOGIN_SUCCESS)

    def test_no_prompts_with_args(self):
        """Testing no prompts with args passed."""
        server_out = StringIO()
        with requests_mock.Mocker() as mocker:
            mocker.post(self.login_url, status_code=200, json=self.success_json)
            lhc = LoginHostCommand(SUBPARSER)
            args = Namespace(username="admin", password="pass")
            with redirect_stdout(server_out):
                lhc.main(args)
                result = server_out.getvalue().rstrip()
                self.assertEqual(result, messages.LOGIN_SUCCESS)
