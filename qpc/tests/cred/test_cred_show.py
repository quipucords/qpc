"""Test the CLI module."""

import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest
import requests
import requests_mock

from qpc.cred import CREDENTIAL_URI
from qpc.cred.show import CredShowCommand
from qpc.tests.utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config


class TestCredentialShowCli:
    """Class for testing the credential show commands for qpc."""

    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = CredShowCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def teardown_method(self, _test_method):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_show_cred_ssl_err(self):
        """Testing the show credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)

            args = Namespace(name="credential1")
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)

    def test_show_cred_conn_err(self):
        """Testing the show credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)

            args = Namespace(name="credential1")
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)

    def test_show_cred_internal_err(self):
        """Testing the show credential command with an internal error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={"error": ["Server Error"]})

            args = Namespace(name="credential1")
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)

    def test_show_cred_empty(self):
        """Testing the show credential command successfully with empty data."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})

            args = Namespace(name="cred1")
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)

    def test_show_cred_data(self):
        """Testing the show credential command with stubbed data."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        credential_entry = {
            "id": 1,
            "name": "cred1",
            "username": "root",
        }
        results = [credential_entry]
        data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)

            args = Namespace(name="cred1")
            with redirect_stdout(cred_out):
                self.command.main(args)
                expected = '{"id":1,"name":"cred1","username":"root"}'
                assert (
                    cred_out.getvalue().replace("\n", "").replace(" ", "").strip()
                    == expected
                )
