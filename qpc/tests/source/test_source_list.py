"""Test the CLI module."""

import logging
import sys
from argparse import ArgumentParser, Namespace  # noqa: I100
from io import StringIO

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.request import CONNECTION_ERROR_MSG
from qpc.source import SOURCE_URI
from qpc.source.list import SourceListCommand
from qpc.tests.utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config


class TestSourceListCli:
    """Class for testing the source list commands for qpc."""

    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = SourceListCommand(subparser)

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

    def test_list_source_ssl_err(self):
        """Testing the list source command with a connection error."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            args = Namespace()
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == CONNECTION_ERROR_MSG

    def test_list_source_conn_err(self):
        """Testing the list source command with a connection error."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)
            args = Namespace()
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == CONNECTION_ERROR_MSG

    def test_list_source_internal_err(self):
        """Testing the list source command with an internal error."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={"error": ["Server Error"]})
            args = Namespace()
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == "Server Error"

    def test_list_source_empty(self, caplog):
        """Testing the list source command successfully with empty data."""
        url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})
            args = Namespace()
            with caplog.at_level(logging.ERROR):
                self.command.main(args)
                assert messages.SOURCE_LIST_NO_SOURCES in caplog.text

    def test_list_source_data(self):
        """Testing the list source command successfully with stubbed data."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI
        source_entry = {
            "id": 1,
            "name": "source1",
            "hosts": ["1.2.3.4"],
            "credentials": [{"id": 1, "name": "cred1"}],
        }
        results = [source_entry]
        next_link = "http://127.0.0.1:8000/api/v1/sources/?page=2"
        data = {"count": 1, "next": next_link, "results": results}
        data2 = {"count": 1, "next": None, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            mocker.get(next_link, status_code=200, json=data2)
            args = Namespace()
            with redirect_stdout(source_out):
                self.command.main(args)
                expected = (
                    '[{"credentials":[{"id":1,"name":"cred1"}],'
                    '"hosts":["1.2.3.4"],"id":1,"name":"source1"}]'
                )
                assert (
                    source_out.getvalue().replace("\n", "").replace(" ", "").strip()
                    == expected + expected
                )

    def test_list_filtered_source_data(self):
        """Testing the list source with filter by source_type."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI
        source_entry = {
            "id": 1,
            "name": "source1",
            "source_type": "network",
            "hosts": ["1.2.3.4"],
            "credentials": [{"id": 1, "name": "cred1"}],
        }
        results = [source_entry]
        data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json=data)
            args = Namespace(type="network")
            with redirect_stdout(source_out):
                self.command.main(args)
                expected = (
                    '[{"credentials":[{"id":1,"name":"cred1"}],'
                    '"hosts":["1.2.3.4"],"id":1,"name":"source1",'
                    '"source_type":"network"}]'
                )
                assert (
                    source_out.getvalue().replace("\n", "").replace(" ", "").strip()
                    == expected
                )
