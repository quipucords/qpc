"""Test the CLI module."""

import logging
import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.request import CONNECTION_ERROR_MSG
from qpc.scan import SCAN_JOB_URI
from qpc.scan.cancel import ScanCancelCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config


class TestScanCancelCli:
    """Class for testing the scan cancel commands for qpc."""

    def _init_command(self):
        """Initialize command."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        return ScanCancelCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        # different from most other test cases where command is initialized once per
        # class, this one requires to be initialized for each test method because
        # SourceEditCommand instance modifies req_path on the fly. This seems to be a
        # code smell to me, but I'm choosing to ignore it for now
        self.command = self._init_command()

        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def teardown_method(self, _test_method):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_cancel_scan_ssl_err(self):
        """Testing the cancel scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_JOB_URI + "1/cancel/"
        with requests_mock.Mocker() as mocker:
            mocker.put(url, exc=requests.exceptions.SSLError)

            args = Namespace(id="1")
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == CONNECTION_ERROR_MSG

    def test_cancel_scan_conn_err(self):
        """Testing the cancel scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_JOB_URI + "1/cancel/"
        with requests_mock.Mocker() as mocker:
            mocker.put(url, exc=requests.exceptions.ConnectTimeout)

            args = Namespace(id="1")
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == CONNECTION_ERROR_MSG

    def test_cancel_scan_internal_err(self):
        """Testing the cancel scan command with an internal error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_JOB_URI + "1/cancel/"
        with requests_mock.Mocker() as mocker:
            mocker.put(url, status_code=500, json={"error": ["Server Error"]})

            args = Namespace(id="1")
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == "Server Error"

    def test_cancel_scan_data(self, caplog):
        """Testing the cancel scan command successfully with stubbed data."""
        url = get_server_location() + SCAN_JOB_URI + "1/cancel/"
        with requests_mock.Mocker() as mocker:
            mocker.put(url, status_code=200, json=None)

            args = Namespace(id="1")
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SCAN_CANCELED % "1"
                assert expected_message in caplog.text
