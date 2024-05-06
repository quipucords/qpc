"""Test the CLI module."""

import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest
import requests_mock

from qpc import messages
from qpc.cli import CLI
from qpc.scan import SCAN_URI
from qpc.scan.start import ScanStartCommand
from qpc.tests.utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config


class TestScanStartCli:
    """Class for testing the scan start commands for qpc."""

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = ScanStartCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def teardown_method(self, _test_method):
        """Tear down test case setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_start_req_args_err(self):
        """Testing the scan start command required flags."""
        with pytest.raises(SystemExit):
            sys.argv = ["/bin/qpc", "scan", "start", "--name", "scan1"]
            CLI().main()

    def test_scan_with_scan_none(self):
        """Testing the scan start command for none existing source."""
        scan_out = StringIO()
        url = get_server_location() + SCAN_URI
        url_post = get_server_location() + SCAN_URI + "1/"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})
            mocker.post(url_post, status_code=300, json=None)

            args = Namespace(name="scan_none")
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert 'Scan "scan_none" does not exist.' in scan_out.getvalue()

    def test_start_scan(self):
        """Testing the start scan command successfully."""
        url_get_scan = get_server_location() + SCAN_URI
        url_post = get_server_location() + SCAN_URI + "1/jobs/"
        results = [
            {
                "id": 1,
                "name": "scan1",
                "sources": ["source1"],
                "disable-optional-products": {"jboss-eap": False, "jboss-fuse": False},
            }
        ]
        scan_data = {"count": 1, "results": results}
        captured_stdout = StringIO()
        with requests_mock.Mocker() as mocker, redirect_stdout(captured_stdout):
            mocker.get(url_get_scan, status_code=200, json=scan_data)
            mocker.post(url_post, status_code=201, json={"id": 1})

            args = Namespace(name="scan1")
            self.command.main(args)
            expected_message = messages.SCAN_STARTED % "1"
            assert expected_message in captured_stdout.getvalue()

    def test_unsuccessful_start_scan(self):
        """Testing the start scan command unsuccessfully."""
        scan_out = StringIO()
        url_get_scan = get_server_location() + SCAN_URI
        url_post = get_server_location() + SCAN_URI + "1/jobs/"
        results = [
            {
                "id": 1,
                "name": "scan1",
                "sources": ["source1"],
                "disable-optional-products": {"jboss-eap": False, "jboss-fuse": False},
            }
        ]
        scan_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=200, json=scan_data)
            mocker.post(url_post, status_code=201, json={"id": 1})

            args = Namespace(name="scan2")
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert 'Scan "scan2" does not exist' in scan_out.getvalue()

    def test_start_scan_bad_resp(self):
        """Testing the start scan command with a 500 error."""
        scan_out = StringIO()
        url_get_scan = get_server_location() + SCAN_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_scan, status_code=500, json=None)

            args = Namespace(name="scan1")
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == messages.SERVER_INTERNAL_ERROR
