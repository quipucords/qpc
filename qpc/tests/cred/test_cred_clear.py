"""Test the "cred clear" command"."""

import logging
import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.cred import CREDENTIAL_BULK_DELETE_URI, CREDENTIAL_URI
from qpc.cred.clear import CredClearCommand
from qpc.tests.mixins import BulkClearTestsMixin
from qpc.tests.utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config


class TestCredentialClearCli(BulkClearTestsMixin):
    """Class for testing the credential clear commands for qpc."""

    _uri_object_root = CREDENTIAL_URI
    _uri_bulk_delete = CREDENTIAL_BULK_DELETE_URI
    _message_no_objects_to_remove = messages.CRED_NO_CREDS_TO_REMOVE
    _message_clear_all_summary = messages.CRED_CLEAR_ALL_SUMMARY
    _message_clear_all_skipped = messages.CRED_CLEAR_ALL_SKIPPED_ASSIGNED_TO_SOURCE
    _bulk_delete_name = "credential"
    _bulk_delete_skipped_because_name = "source"

    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = CredClearCommand(subparser)

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

    def test_clear_cred_ssl_err(self):
        """Testing the clear credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            args = Namespace(name="credential1")
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)

    def test_clear_cred_conn_err(self):
        """Testing the clear credential command with a connection error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            args = Namespace(name="credential1")
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)

    def test_clear_cred_internal_err(self):
        """Testing the clear credential command with an internal error."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={"error": ["Server Error"]})
            args = Namespace(name="credential1")
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)

    def test_clear_cred_empty(self):
        """Testing the clear credential command with empty data."""
        cred_out = StringIO()
        url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})
            args = Namespace(name="cred1")
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)

    def test_clear_by_name(self, caplog):
        """Testing the clear credential command with stubbed data."""
        get_url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        delete_url = get_server_location() + CREDENTIAL_URI + "1/"
        credential_entry = {
            "id": 1,
            "name": "credential1",
            "username": "root",
            "password": "********",
        }
        results = [credential_entry]
        data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=204)
            args = Namespace(name="credential1")
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.CRED_REMOVED % "credential1"
                assert expected_message in caplog.text

    def test_clear_by_name_err(self):
        """Testing the clear credential command successfully with stubbed data.

        When specifying a name with an error response
        """
        cred_out = StringIO()
        get_url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        delete_url = get_server_location() + CREDENTIAL_URI + "1/"
        credential_entry = {
            "id": 1,
            "name": "credential1",
            "username": "root",
            "password": "********",
        }
        results = [credential_entry]
        data = {"count": 1, "results": results}
        err_data = {"error": ["Server Error"]}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)
            args = Namespace(name="credential1")
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)
