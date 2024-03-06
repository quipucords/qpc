"""Test the CLI module."""

import logging
import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.cred import CREDENTIAL_URI
from qpc.cred.clear import CredClearCommand
from qpc.tests.utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config


class TestCredentialClearCli:
    """Class for testing the credential clear commands for qpc."""

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

    def test_clear_all_empty(self):
        """Testing the clear credential command successfully with stubbed data.

        With empty list of credentials.
        """
        cred_out = StringIO()
        get_url = get_server_location() + CREDENTIAL_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json={"count": 0})
            args = Namespace(name=None)
            with pytest.raises(SystemExit):
                with redirect_stdout(cred_out):
                    self.command.main(args)

    def test_clear_all_but_some_are_skipped(self, faker, caplog):
        """Test "clear all" when some credentials are not deleted."""
        get_url = get_server_location() + CREDENTIAL_URI
        delete_url = get_server_location() + CREDENTIAL_URI + "bulk_delete/"
        all_credential_ids = [
            faker.random_int() for _ in range(faker.random_int(min=5, max=15))
        ]
        get_response = {"count": len(all_credential_ids)}
        skipped = [
            {"credential": cred_id, "sources": [faker.random_int()]}
            for cred_id in faker.random_sample(all_credential_ids)
        ]
        deleted = list(
            set(all_credential_ids)
            - set([skipped_cred["credential"] for skipped_cred in skipped])
        )
        bulk_delete_response = {"deleted": deleted, "skipped": skipped}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=get_response)
            mocker.post(delete_url, status_code=200, json=bulk_delete_response)
            args = Namespace(name=None)
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            for skipped_cred in skipped:
                assert messages.CRED_CLEAR_ALL_SKIPPED_ASSIGNED_TO_SOURCE % {
                    "credential_id": skipped_cred["credential"],
                    "source_ids": skipped_cred["sources"],
                }
            expected_message = messages.CRED_CLEAR_ALL_SUMMARY % {
                "deleted_count": len(deleted),
                "skipped_count": len(skipped),
            }
            assert expected_message in caplog.text

    def test_clear_all_but_unexpected_error_in_initial_get(self, caplog, faker):
        """Test "clear all" when the GET fails unexpectedly before the delete POST."""
        get_url = get_server_location() + CREDENTIAL_URI
        server_error_message = faker.sentence()
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=500, json=server_error_message)
            args = Namespace(name=None)
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert server_error_message in caplog.text

    def test_clear_all_but_unexpected_error_in_bulk_delete(self, caplog):
        """Test "clear all" when an unexpected server error occurs during deletion."""
        get_url = get_server_location() + CREDENTIAL_URI
        delete_url = get_server_location() + CREDENTIAL_URI + "bulk_delete/"
        get_response = {"count": 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=get_response)
            mocker.post(delete_url, status_code=500)
            args = Namespace(name=None)
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert messages.SERVER_INTERNAL_ERROR in caplog.text

    def test_clear_all(self, caplog, faker):
        """Test "clear all" when all credentials are successfully deleted."""
        get_url = get_server_location() + CREDENTIAL_URI
        delete_url = get_server_location() + CREDENTIAL_URI + "bulk_delete/"
        all_credential_ids = [
            faker.random_int() for _ in range(faker.random_int(min=2, max=10))
        ]
        get_response = {"count": len(all_credential_ids)}
        bulk_delete_response = {"deleted": all_credential_ids, "skipped": []}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=get_response)
            mocker.post(delete_url, status_code=200, json=bulk_delete_response)
            args = Namespace(name=None)
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.CRED_CLEAR_ALL_SUMMARY % {
                    "deleted_count": len(all_credential_ids),
                    "skipped_count": 0,
                }
                assert expected_message in caplog.text
