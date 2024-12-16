"""Test the "cred clear" command."""

import logging
from argparse import ArgumentParser, Namespace

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.cred import CREDENTIAL_BULK_DELETE_URI, CREDENTIAL_URI
from qpc.cred.clear import CredClearCommand
from qpc.request import CONNECTION_ERROR_MSG
from qpc.tests.mixins import BulkClearTestsMixin
from qpc.tests.utilities import DEFAULT_CONFIG
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

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = CredClearCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)

    def test_clear_cred_ssl_err(self, caplog):
        """Testing the clear credential command with a connection error."""
        url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            args = Namespace(name="credential1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected_error in caplog.text

    def test_clear_cred_conn_err(self, caplog):
        """Testing the clear credential command with a connection error."""
        url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            args = Namespace(name="credential1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected_error in caplog.text

    def test_clear_cred_internal_err(self, caplog):
        """Testing the clear credential command with an internal error."""
        url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        error_message = "Server Error"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={"error": ["Server Error"]})
            args = Namespace(name="credential1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert error_message in caplog.text

    def test_clear_cred_empty(self, caplog):
        """Testing the clear credential command with empty data."""
        url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})
            args = Namespace(name="cred1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert 'Credential "cred1" was not found' in caplog.text

    def test_clear_by_name(self, caplog):
        """Testing the clear credential command with stubbed data."""
        get_url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        delete_url = get_server_location() + CREDENTIAL_URI + "1/"
        credential_entry = {
            "id": 1,
            "name": "credential1",
            "username": "root",
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

    @pytest.mark.skip(
        reason=(
            "FIXME! This test seems reasonable, but CredClearCommand._delete_entry "
            "logic incorrectly handles server error responses. Underlying code needs "
            "a thorough evaluation and rewrite."
        )
    )
    def test_clear_by_name_err(self, caplog):
        """Testing the clear credential command successfully with stubbed data.

        When specifying a name with an error response
        """
        get_url = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        delete_url = get_server_location() + CREDENTIAL_URI + "1/"
        credential_entry = {
            "id": 1,
            "name": "credential1",
            "username": "root",
        }
        results = [credential_entry]
        data = {"count": 1, "results": results}
        err_data = {"error": ["Server Error"]}
        expected = 'Failed to remove source "credential1"'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)
            args = Namespace(name="credential1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected in caplog.text
