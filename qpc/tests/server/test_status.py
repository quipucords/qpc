"""Test the CLI module."""

import json
import logging
import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest
import requests_mock

from qpc import messages
from qpc.cli import CLI
from qpc.server import STATUS_URI
from qpc.server.status import ServerStatusCommand
from qpc.tests.utilities import redirect_stdout
from qpc.utils import get_server_location


@pytest.mark.usefixtures("server_config")
class TestServerStatus:
    """Class for testing the server status command for qpc."""

    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = ServerStatusCommand(subparser)

    def test_download_server_status(self, caplog, tmp_path):
        """Testing recording server status command in a file."""
        fake_json = tmp_path / "test.json"
        get_status_url = get_server_location() + STATUS_URI
        get_status_json_data = {
            "api_version": 1,
            "build": "a64eee4",
            "environment_vars": {"key": "value"},
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(get_status_url, status_code=200, json=get_status_json_data)

            args = Namespace(path=str(fake_json))
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.STATUS_SUCCESSFULLY_WRITTEN
                assert expected_message in caplog.text
            with fake_json.open("r", encoding="utf-8") as json_file:
                data = json_file.read()
                file_content_dict = json.loads(data)
            assert get_status_json_data == file_content_dict

    def test_print_server_status(self):
        """Testing recording server status command in a file."""
        status_out = StringIO()

        get_status_url = get_server_location() + STATUS_URI
        get_status_json_data = {
            "api_version": 1,
            "build": "a64eee4",
            "environment_vars": {"key": "value"},
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(get_status_url, status_code=200, json=get_status_json_data)

            args = Namespace(path=None)
            with redirect_stdout(status_out):
                self.command.main(args)
                assert json.loads(status_out.getvalue().strip()) == get_status_json_data

    def test_write_status_output_directory_not_exist(self):
        """Testing fail because output directory does not exist."""
        with pytest.raises(SystemExit):
            sys.argv = ["/bin/qpc", "server", "status", "--output-file", "/foo/bar/"]
            CLI().main()

    def test_write_status_output_file_empty(self):
        """Testing fail because output file empty."""
        with pytest.raises(SystemExit):
            sys.argv = ["/bin/qpc", "server", "status", "--output-file"]
            CLI().main()

    def test_status_unexpected_failure(self):
        """Testing getting status with unexpected failure."""
        status_out = StringIO()

        get_status_url = get_server_location() + STATUS_URI
        get_status_json_data = {"api": 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_status_url, status_code=400, json=get_status_json_data)

            args = Namespace(path=None)
            with pytest.raises(SystemExit):
                with redirect_stdout(status_out):
                    self.command.main(args)
                    assert status_out.getvalue() == messages.SERVER_STATUS_FAILURE
