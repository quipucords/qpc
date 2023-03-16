"""Test the CLI module."""

import sys
import unittest
from argparse import ArgumentParser, Namespace
from io import StringIO

import requests
import requests_mock

from qpc import messages
from qpc.request import CONNECTION_ERROR_MSG
from qpc.scan import SCAN_JOB_URI
from qpc.scan.cancel import ScanCancelCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest="subcommand")


class ScanCancelCliTests(unittest.TestCase):
    """Class for testing the scan cancel commands for qpc."""

    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_cancel_scan_ssl_err(self):
        """Testing the cancel scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_JOB_URI + "1/cancel/"
        with requests_mock.Mocker() as mocker:
            mocker.put(url, exc=requests.exceptions.SSLError)
            nsc = ScanCancelCommand(SUBPARSER)
            args = Namespace(id="1")
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    nsc.main(args)
                    self.assertEqual(scan_out.getvalue(), CONNECTION_ERROR_MSG)

    def test_cancel_scan_conn_err(self):
        """Testing the cancel scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_JOB_URI + "1/cancel/"
        with requests_mock.Mocker() as mocker:
            mocker.put(url, exc=requests.exceptions.ConnectTimeout)
            nsc = ScanCancelCommand(SUBPARSER)
            args = Namespace(id="1")
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    nsc.main(args)
                    self.assertEqual(scan_out.getvalue(), CONNECTION_ERROR_MSG)

    def test_cancel_scan_internal_err(self):
        """Testing the cancel scan command with an internal error."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_JOB_URI + "1/cancel/"
        with requests_mock.Mocker() as mocker:
            mocker.put(url, status_code=500, json={"error": ["Server Error"]})
            nsc = ScanCancelCommand(SUBPARSER)
            args = Namespace(id="1")
            with self.assertRaises(SystemExit):
                with redirect_stdout(scan_out):
                    nsc.main(args)
                    self.assertEqual(scan_out.getvalue(), "Server Error")

    def test_cancel_scan_data(self):
        """Testing the cancel scan command successfully with stubbed data."""
        url = get_server_location() + SCAN_JOB_URI + "1/cancel/"
        with requests_mock.Mocker() as mocker:
            mocker.put(url, status_code=200, json=None)
            nsc = ScanCancelCommand(SUBPARSER)
            args = Namespace(id="1")
            with self.assertLogs(level="INFO") as log:
                nsc.main(args)
                expected_message = messages.SCAN_CANCELED % "1"
                self.assertIn(expected_message, log.output[-1])
