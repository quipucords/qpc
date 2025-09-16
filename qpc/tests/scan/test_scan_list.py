"""Test the CLI module."""

import logging
import sys
from argparse import ArgumentParser, Namespace  # noqa: I001
from io import StringIO

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.request import CONNECTION_ERROR_MSG
from qpc.scan import SCAN_URI
from qpc.scan.list import ScanListCommand
from qpc.tests.utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config


class TestScanListCli:
    """Class for testing the scan list commands for qpc."""

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = ScanListCommand(subparser)

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

    def test_list_scan_ssl_err(self):
        """Testing the list scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)

            args = Namespace()
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == CONNECTION_ERROR_MSG

    def test_list_scan_conn_err(self):
        """Testing the list scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)

            args = Namespace()
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == CONNECTION_ERROR_MSG

    def test_list_scan_internal_err(self):
        """Testing the list scan command with an internal error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={"error": ["Server Error"]})

            args = Namespace()
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == "Server Error"

    def test_list_scan_empty(self, caplog):
        """Testing the list scan command successfully with empty data."""
        url = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})

            args = Namespace()
            with caplog.at_level(logging.ERROR):
                self.command.main(args)
                assert messages.SCAN_LIST_NO_SCANS in caplog.text

    def test_list_scan_data(self):
        """Testing the list scan command successfully with stubbed data."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        scan_entry = {
            "id": 1,
            "scan_type": "inspect",
            "source": {"id": 1, "name": "scan1"},
        }
        results = [scan_entry]
        next_link = get_server_location() + SCAN_URI + "?page=2"
        data = {"count": 1, "next": next_link, "results": results}
        data2 = {"count": 1, "next": None, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            mocker.get(next_link, status_code=200, json=data2)

            args = Namespace()
            args.output_table = False
            with redirect_stdout(scan_out):
                self.command.main(args)
                expected = (
                    '[{"id":1,"scan_type":"inspect","source":{"id":1,"name":"scan1"}}]'
                )
                assert (
                    scan_out.getvalue().replace("\n", "").replace(" ", "").strip()
                    == expected + expected
                )

    def test_list_filter_type(self):
        """Testing the list scan with filter by type."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        scan_entry = {
            "id": 1,
            "scan_type": "inspect",
            "source": {"id": 1, "name": "scan1"},
        }
        results = [scan_entry]
        data = {"count": 1, "next": None, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)

            args = Namespace(type="inspect")
            args.output_table = False
            with redirect_stdout(scan_out):
                self.command.main(args)
                expected = (
                    '[{"id":1,"scan_type":"inspect","source":{"id":1,"name":"scan1"}}]'
                )
                assert (
                    scan_out.getvalue().replace("\n", "").replace(" ", "").strip()
                    == expected
                )
