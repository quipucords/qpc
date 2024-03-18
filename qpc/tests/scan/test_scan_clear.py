"""Test the "scan clear" commands."""

import logging
import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.request import CONNECTION_ERROR_MSG
from qpc.scan import SCAN_BULK_DELETE_URI, SCAN_URI
from qpc.scan.clear import ScanClearCommand
from qpc.tests.utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config


class TestScanClearCli:
    """Class for testing the scan clear commands for qpc."""

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = ScanClearCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def teaddown_method(self, _test_method):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_clear_scan_ssl_err(self):
        """Testing the clear scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI + "?name=scan1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)

            args = Namespace(name="scan1")
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == CONNECTION_ERROR_MSG

    def test_clear_scan_conn_err(self):
        """Testing the clear scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI + "?name=scan1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)

            args = Namespace(name="scan1")
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == CONNECTION_ERROR_MSG

    def test_clear_scan_internal_err(self):
        """Testing the clear scan command with an internal error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI + "?name=scan1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={"error": ["Server Error"]})

            args = Namespace(name="scan1")
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == "Server Error"

    def test_clear_scan_empty(self):
        """Testing the clear scan command successfully with empty data."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI + "?name=scan1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})

            args = Namespace(name="scan1")
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == 'scan "scan1" was not found\n'

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

    def test_clear_by_name_err(self):
        """Test the clear scan command successfully.

        With stubbed data when specifying a name with an error response
        """
        scan_out = StringIO()
        get_url = get_server_location() + SCAN_URI + "?name=scan1"
        delete_url = get_server_location() + SCAN_URI + "1/"
        scan_entry = {"id": 1, "name": "scan1", "sources": ["source1"]}
        results = [scan_entry]
        data = {"count": 1, "results": results}
        err_data = {"error": ["Server Error"]}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)

            args = Namespace(name="scan1")
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    expected = 'Failed to remove scan "scan1"'
                    assert expected in scan_out.getvalue()

    def test_clear_all_empty(self):
        """Test the clear scan command successfully.

        With stubbed data empty list of scans
        """
        scan_out = StringIO()
        get_url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json={"count": 0})

            args = Namespace(name=None)
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    expected = "No scans exist to be removed\n"
                    assert scan_out.getvalue() == expected

    def test_clear_all_but_unexpected_error_in_initial_get(self, caplog, faker):
        """Test "clear all" when the GET fails unexpectedly before the delete POST."""
        get_url = get_server_location() + SCAN_URI
        server_error_message = faker.sentence()
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=500, json=server_error_message)
            args = Namespace(name=None)
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert server_error_message in caplog.text

    def test_clear_all(self, caplog, faker):
        """Test "clear all" when all scans are successfully deleted."""
        get_url = get_server_location() + SCAN_URI
        delete_url = get_server_location() + SCAN_BULK_DELETE_URI
        all_scan_ids = [
            faker.random_int() for _ in range(faker.random_int(min=2, max=10))
        ]
        get_response = {"count": len(all_scan_ids)}
        bulk_delete_response = {"deleted": all_scan_ids}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=get_response)
            mocker.post(delete_url, status_code=200, json=bulk_delete_response)
            args = Namespace(name=None)
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SCAN_CLEAR_ALL_SUMMARY % {
                    "deleted_count": len(all_scan_ids)
                }
                assert expected_message in caplog.text
