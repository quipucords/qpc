"""Test the "scan clear" command."""

import logging
from argparse import ArgumentParser, Namespace

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.request import CONNECTION_ERROR_MSG
from qpc.scan import SCAN_BULK_DELETE_URI, SCAN_URI
from qpc.scan.clear import ScanClearCommand
from qpc.tests.mixins import BulkClearTestsMixin
from qpc.tests.utilities import DEFAULT_CONFIG
from qpc.utils import get_server_location, write_server_config


class TestScanClearCli(BulkClearTestsMixin):
    """Class for testing the scan clear commands for qpc."""

    _uri_object_root = SCAN_URI
    _uri_bulk_delete = SCAN_BULK_DELETE_URI
    _message_no_objects_to_remove = messages.SCAN_NO_SCANS_TO_REMOVE
    _message_clear_all_summary = messages.SCAN_CLEAR_ALL_SUMMARY
    _message_clear_all_skipped = None  # does not apply for scans
    _bulk_delete_name = "scan"
    _bulk_delete_skipped_because_name = None  # does not apply for scans

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = ScanClearCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)

    def test_clear_scan_ssl_err(self, caplog):
        """Testing the clear scan command with a connection error."""
        url = get_server_location() + SCAN_URI + "?name=scan1"
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)

            args = Namespace(name="scan1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected_error in caplog.text

    def test_clear_scan_conn_err(self, caplog):
        """Testing the clear scan command with a connection error."""
        url = get_server_location() + SCAN_URI + "?name=scan1"
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)

            args = Namespace(name="scan1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected_error in caplog.text

    def test_clear_scan_internal_err(self, caplog):
        """Testing the clear scan command with an internal error."""
        url = get_server_location() + SCAN_URI + "?name=scan1"
        error_message = "Server Error"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={"error": [error_message]})

            args = Namespace(name="scan1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert error_message in caplog.text

    def test_clear_scan_empty(self, caplog):
        """Testing the clear scan command successfully with empty data."""
        url = get_server_location() + SCAN_URI + "?name=scan1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})

            args = Namespace(name="scan1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert 'Scan "scan1" was not found' in caplog.text

    def test_clear_by_name(self, caplog):
        """Testing the clear scan command.

        Successfully with stubbed data when specifying a name
        """
        get_url = get_server_location() + SCAN_URI + "?name=scan1"
        delete_url = get_server_location() + SCAN_URI + "1/"
        scan_entry = {"id": 1, "name": "scan1", "sources": ["source1"]}
        results = [scan_entry]
        data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=204)

            args = Namespace(name="scan1")
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_msg = messages.SCAN_REMOVED % "scan1"
                assert expected_msg in caplog.text

    @pytest.mark.skip(
        reason=(
            "FIXME! This test seems reasonable, but ScanClearCommand._delete_entry "
            "logic incorrectly handles server error responses. Underlying code needs "
            "a thorough evaluation and rewrite."
        )
    )
    def test_clear_by_name_err(self, caplog):
        """Test the clear scan command successfully.

        With stubbed data when specifying a name with an error response
        """
        get_url = get_server_location() + SCAN_URI + "?name=scan1"
        delete_url = get_server_location() + SCAN_URI + "1/"
        scan_entry = {"id": 1, "name": "scan1", "sources": ["source1"]}
        results = [scan_entry]
        data = {"count": 1, "results": results}
        err_data = {"error": ["Server Error"]}
        expected = 'Failed to remove source "scan1"'
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)

            args = Namespace(name="scan1")
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected in caplog.text
