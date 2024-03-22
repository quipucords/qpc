"""Test the "source clear" commands."""

import logging
from argparse import ArgumentParser, Namespace

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.request import CONNECTION_ERROR_MSG
from qpc.source import SOURCE_BULK_DELETE_URI, SOURCE_URI
from qpc.source.clear import SourceClearCommand
from qpc.tests.mixins import BulkClearTestsMixin
from qpc.tests.utilities import DEFAULT_CONFIG
from qpc.utils import get_server_location, write_server_config


class TestSourceClearCli(BulkClearTestsMixin):
    """Class for testing the source clear commands for qpc."""

    _uri_object_root = SOURCE_URI
    _uri_bulk_delete = SOURCE_BULK_DELETE_URI
    _message_no_objects_to_remove = messages.SOURCE_NO_SOURCES_TO_REMOVE
    _message_clear_all_summary = messages.SOURCE_CLEAR_ALL_SUMMARY
    _message_clear_all_skipped = messages.SOURCE_CLEAR_ALL_SKIPPED_ASSIGNED_TO_SCAN
    _bulk_delete_name = "source"
    _bulk_delete_skipped_because_name = "scan"

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = SourceClearCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)

    def test_clear_source_ssl_err(self, caplog):
        """Testing the clear source command with a connection error."""
        url = get_server_location() + SOURCE_URI + "?name=source1"
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)

            args = Namespace(name="source1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected_error in caplog.text

    def test_clear_source_conn_err(self, caplog):
        """Testing the clear source command with a connection error."""
        url = get_server_location() + SOURCE_URI + "?name=source1"
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)

            args = Namespace(name="source1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected_error in caplog.text

    def test_clear_source_internal_err(self, caplog):
        """Testing the clear source command with an internal error."""
        url = get_server_location() + SOURCE_URI + "?name=source1"
        error_message = "Server Error"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={"error": [error_message]})

            args = Namespace(name="source1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert error_message in caplog.text

    def test_clear_source_empty(self, caplog):
        """Testing the clear source command successfully with empty data."""
        url = get_server_location() + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})

            args = Namespace(name="source1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert 'Source "source1" was not found' in caplog.text

    def test_clear_by_name(self, caplog):
        """Testing the clear source command.

        Successfully with stubbed data when specifying a name
        """
        get_url = get_server_location() + SOURCE_URI + "?name=source1"
        delete_url = get_server_location() + SOURCE_URI + "1/"
        source_entry = {
            "id": 1,
            "name": "source1",
            "hosts": ["1.2.3.4"],
            "credential": ["credential1", "cred2"],
            "port": 22,
        }
        results = [source_entry]
        data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=204)

            args = Namespace(name="source1")
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_REMOVED % "source1"
                assert expected_message in caplog.text

    @pytest.mark.skip(
        reason=(
            "FIXME! This test seems reasonable, but SourceClearCommand._delete_entry "
            "logic incorrectly handles server error responses. Underlying code needs "
            "a thorough evaluation and rewrite."
        )
    )
    def test_clear_by_name_err(self, caplog):
        """Test the clear source command successfully.

        With stubbed data when specifying a name with an error response
        """
        get_url = get_server_location() + SOURCE_URI + "?name=source1"
        delete_url = get_server_location() + SOURCE_URI + "1/"
        source_entry = {
            "id": 1,
            "name": "source1",
            "hosts": ["1.2.3.4"],
            "credential": ["credential1", "cred2"],
            "port": 22,
        }
        results = [source_entry]
        data = {"count": 1, "results": results}
        err_data = {"error": ["Server Error"]}
        expected = 'Failed to remove source "source1"'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)

            args = Namespace(name="source1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected in caplog.text
