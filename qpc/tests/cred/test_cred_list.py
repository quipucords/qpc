"""Test the CLI module."""

import logging
import sys
from argparse import ArgumentParser, Namespace  # noqa: I100
from io import StringIO

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.cred import CREDENTIAL_URI
from qpc.cred.list import CredListCommand
from qpc.tests.utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config


class TestCredentialListCli:
    """Class for testing the credential list commands for qpc."""

    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = CredListCommand(subparser)

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

    def test_list_cred_ssl_err(self):
        """Testing the list credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)

            args = Namespace()
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)

    def test_list_cred_conn_err(self):
        """Testing the list credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)

            args = Namespace()
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)

    def test_list_cred_internal_err(self):
        """Testing the list credential command with an internal error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={"error": ["Server Error"]})

            args = Namespace()
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)

    def test_list_cred_empty(self, caplog):
        """Testing the list credential command successfully with empty data."""
        url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})

            args = Namespace()
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.CRED_LIST_NO_CREDS
                assert expected_message in caplog.text

    def test_list_cred_data(self):
        """Testing the list credential command with stubbed data."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        credential_entry = {
            "id": 1,
            "name": "cred1",
            "username": "root",
            "password": "********",
        }
        results = [credential_entry]
        next_link = "http://127.0.0.1:8000/api/v2/credentials/?page=2"
        data = {"count": 1, "next": next_link, "results": results}
        data2 = {"count": 1, "next": None, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            mocker.get(next_link, status_code=200, json=data2)

            args = Namespace()
            with redirect_stdout(cred_out):
                self.command.main(args)
                expected = (
                    '[{"id":1,"name":"cred1","password":"********",'
                    '"username":"root"}]'
                )
                assert (
                    cred_out.getvalue().replace("\n", "").replace(" ", "").strip()
                    == expected + expected
                )

    def test_list_filtered_cred_data(self):
        """Testing the list credential with filter by cred type."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI
        credential_entry = {
            "id": 1,
            "name": "cred1",
            "cred_type": "network",
            "username": "root",
            "password": "********",
        }
        results = [credential_entry]
        data = {"count": 1, "next": None, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)

            args = Namespace(type="network")
            with redirect_stdout(cred_out):
                self.command.main(args)
                expected = (
                    '[{"cred_type":"network","id":1,'
                    '"name":"cred1","password":"********",'
                    '"username":"root"}]'
                )
                assert (
                    cred_out.getvalue().replace("\n", "").replace(" ", "").strip()
                    == expected
                )
