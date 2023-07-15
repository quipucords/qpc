"""Test the CLI module."""

import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest
import requests
import requests_mock

from qpc.request import CONNECTION_ERROR_MSG
from qpc.source import SOURCE_URI
from qpc.source.show import SourceShowCommand
from qpc.tests_utilities import HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config


class TestSourceShowCli:
    """Class for testing the source show commands for qpc."""

    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = SourceShowCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        # Temporarily disable stderr for these tests, CLI errors clutter up
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()
        write_server_config({"host": "127.0.0.1", "port": 8000, "use_http": True})
        self.base_url = get_server_location()

    def teardown_method(self, _test_method):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_show_source_ssl_err(self):
        """Testing the show source command with a connection error."""
        source_out = StringIO()
        url = self.base_url + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            args = Namespace(name="source1")
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == CONNECTION_ERROR_MSG

    def test_show_source_conn_err(self):
        """Testing the show source command with a connection error."""
        source_out = StringIO()
        url = self.base_url + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            args = Namespace(name="source1")
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == CONNECTION_ERROR_MSG

    def test_show_source_internal_err(self):
        """Testing the show source command with an internal error."""
        source_out = StringIO()
        url = self.base_url + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={"error": ["Server Error"]})
            args = Namespace(name="source1")
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == "Server Error"

    def test_show_source_empty(self):
        """Testing the show source command successfully with empty data."""
        source_out = StringIO()
        url = self.base_url + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})
            args = Namespace(name="source1")
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == 'Source "source1" does not exist\n'

    def test_show_source_data(self):
        """Testing the show source command successfully with stubbed data."""
        source_out = StringIO()
        url = self.base_url + SOURCE_URI + "?name=source1"
        source_entry = {
            "id": 1,
            "name": "source1",
            "hosts": ["1.2.3.4"],
            "credentials": [{"id": 1, "name": "cred1"}],
        }
        results = [source_entry]
        data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            args = Namespace(name="source1")
            with redirect_stdout(source_out):
                self.command.main(args)
                expected = (
                    '{"credentials":[{"id":1,"name":"cred1"}],'
                    '"hosts":["1.2.3.4"],"id":1,"name":"source1"}'
                )
                assert (
                    source_out.getvalue().replace("\n", "").replace(" ", "").strip()
                    == expected
                )
