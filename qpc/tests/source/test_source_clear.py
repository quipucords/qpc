"""Test the "source clear" commands."""

import logging
import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.request import CONNECTION_ERROR_MSG
from qpc.source import SOURCE_BULK_DELETE_URI, SOURCE_URI
from qpc.source.clear import SourceClearCommand
from qpc.tests.utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config


class TestSourceClearCli:
    """Class for testing the source clear commands for qpc."""

    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = SourceClearCommand(subparser)

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

    def test_clear_source_ssl_err(self):
        """Testing the clear source command with a connection error."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)

            args = Namespace(name="source1")
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == CONNECTION_ERROR_MSG

    def test_clear_source_conn_err(self):
        """Testing the clear source command with a connection error."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)

            args = Namespace(name="source1")
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == CONNECTION_ERROR_MSG

    def test_clear_source_internal_err(self):
        """Testing the clear source command with an internal error."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=500, json={"error": ["Server Error"]})

            args = Namespace(name="source1")
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == "Server Error"

    def test_clear_source_empty(self):
        """Testing the clear source command successfully with empty data."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})

            args = Namespace(name="source1")
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == 'Source "source1" was not found\n'

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

    def test_clear_by_name_err(self):
        """Test the clear source command successfully.

        With stubbed data when specifying a name with an error response
        """
        source_out = StringIO()
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
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=data)
            mocker.delete(delete_url, status_code=500, json=err_data)

            args = Namespace(name="source1")
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    expected = 'Failed to remove source "source1"'
                    assert expected in source_out.getvalue()

    def test_clear_all_empty(self):
        """Test the clear source command successfully.

        With stubbed data empty list of sources
        """
        source_out = StringIO()
        get_url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json={"count": 0})

            args = Namespace(name=None)
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    expected = "No sources exist to be removed\n"
                    assert source_out.getvalue() == expected

    def test_clear_all_but_some_are_skipped(self, faker, caplog):
        """Test "clear all" when some sources are not deleted."""
        get_url = get_server_location() + SOURCE_URI
        delete_url = get_server_location() + SOURCE_URI + "bulk_delete/"
        all_source_ids = [
            faker.random_int() for _ in range(faker.random_int(min=5, max=15))
        ]
        get_response = {"count": len(all_source_ids)}
        skipped = [
            {"source": source_id, "scans": [faker.random_int()]}
            for source_id in faker.random_sample(all_source_ids)
        ]
        deleted = list(
            set(all_source_ids)
            - set([skipped_source["source"] for skipped_source in skipped])
        )
        bulk_delete_response = {"deleted": deleted, "skipped": skipped}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=get_response)
            mocker.post(delete_url, status_code=200, json=bulk_delete_response)
            args = Namespace(name=None)
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            for skipped_source in skipped:
                assert messages.SOURCE_CLEAR_ALL_SKIPPED_ASSIGNED_TO_SCAN % {
                    "source_id": skipped_source["source"],
                    "scan_ids": skipped_source["scans"],
                }
            expected_message = messages.SOURCE_CLEAR_ALL_SUMMARY % {
                "deleted_count": len(deleted),
                "skipped_count": len(skipped),
            }
            assert expected_message in caplog.text

    def test_clear_all_but_unexpected_error_in_initial_get(self, caplog, faker):
        """Test "clear all" when the GET fails unexpectedly before the delete POST."""
        get_url = get_server_location() + SOURCE_URI
        server_error_message = faker.sentence()
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=500, json=server_error_message)
            args = Namespace(name=None)
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert server_error_message in caplog.text

    def test_clear_all(self, caplog, faker):
        """Test "clear all" when all sources are successfully deleted."""
        get_url = get_server_location() + SOURCE_URI
        delete_url = get_server_location() + SOURCE_BULK_DELETE_URI
        all_source_ids = [
            faker.random_int() for _ in range(faker.random_int(min=2, max=10))
        ]
        get_response = {"count": len(all_source_ids)}
        bulk_delete_response = {"deleted": all_source_ids, "skipped": []}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=get_response)
            mocker.post(delete_url, status_code=200, json=bulk_delete_response)
            args = Namespace(name=None)
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_CLEAR_ALL_SUMMARY % {
                    "deleted_count": len(all_source_ids),
                    "skipped_count": 0,
                }
                assert expected_message in caplog.text
