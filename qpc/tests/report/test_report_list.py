"""Test the CLI report list subcommand."""

import json
import logging
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from unittest.mock import patch

import pytest
import requests_mock

from qpc import messages
from qpc.cli import CLI
from qpc.report import REPORT_V2_URI
from qpc.report.list import MIN_SERVER_VERSION, ReportListCommand
from qpc.utils import get_server_location

VERSION = MIN_SERVER_VERSION


@pytest.fixture
def json_file_path(tmp_path) -> str:
    """Return a fake json file path string."""
    return str(tmp_path / "test.json")


@pytest.fixture
def get_report_url() -> str:
    """Return a list report url."""
    return get_server_location() + REPORT_V2_URI


@pytest.fixture
def report_json_data() -> dict:
    """Return a sample report json."""
    return {
        "count": 3,
        "next": None,
        "previous": None,
        "results": [
            {"id": 1, "can_publish": True, "origin": "local"},
            {"id": 2, "can_publish": False, "cannot_publish_reason": "bad report"},
            {"id": 3, "can_publish": True, "origin": "local"},
        ],
    }


@pytest.mark.usefixtures("server_config")
class TestReportListCommand:
    """Class for testing the list report command."""

    def _init_command(self):
        """Initialize command."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        return ReportListCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        self.command = self._init_command()

    def test_list_report_as_json(
        self, caplog, json_file_path, get_report_url, report_json_data
    ):
        """Testing retrieving the list of reports as json."""
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=200,
                json=report_json_data,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                report_id=1,
                path=json_file_path,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.REPORT_SUCCESSFULLY_WRITTEN in caplog.text
                with Path(json_file_path).open("r", encoding="utf-8") as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                assert report_json_data == file_content_dict

    # Test validation
    def test_list_report_output_directory(self):
        """Testing fail because output file is a directory."""
        with pytest.raises(SystemExit):
            sys.argv = [
                "/bin/qpc",
                "report",
                "list",
                "--output-file",
                "/",
            ]
            CLI().main()

    def test_list_report_output_directory_not_exist(self):
        """Testing fail because output directory does not exist."""
        with pytest.raises(SystemExit):
            sys.argv = [
                "/bin/qpc",
                "report",
                "list",
                "--output-file",
                "/foo/bar/",
            ]
            CLI().main()

    def test_list_report_output_file_empty(self):
        """Testing fail because output file empty."""
        with pytest.raises(SystemExit):
            sys.argv = [
                "/bin/qpc",
                "report",
                "list",
                "--output-file",
                "",
            ]
            CLI().main()

    @patch("qpc.report.list.write_file")
    def test_list_file_fails_to_write(
        self, file, caplog, json_file_path, get_report_url, report_json_data
    ):
        """Testing list failure while writing to file."""
        file.side_effect = EnvironmentError()
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=200,
                json=report_json_data,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                path=json_file_path,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.WRITE_FILE_ERROR % {
                    "path": json_file_path,
                    "error": "",
                }
                assert err_msg in caplog.text

    def test_list_nonexistent_directory(
        self, caplog, json_file_path, get_report_url, report_json_data
    ):
        """Testing error for nonexistent directory in output."""
        fake_dir = "/cody/is/awesome/list.json"
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200, json=report_json_data)

            args = Namespace(
                path=fake_dir,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = (
                    messages.REPORT_DIRECTORY_DOES_NOT_EXIST % Path(fake_dir).parent
                )
                assert err_msg in caplog.text

    def test_list_non_json_path(
        self, caplog, json_file_path, get_report_url, report_json_data
    ):
        """Testing error for non json file path."""
        non_json_dir = "/Users/list.tar.gz"
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200, json=report_json_data)

            args = Namespace(
                path=non_json_dir,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.OUTPUT_FILE_TYPE % ".json"
                assert err_msg in caplog.text

    def test_list_old_version(
        self, caplog, json_file_path, get_report_url, report_json_data
    ):
        """Test server version is too old."""
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=400,
                headers={"X-Server-Version": "0.0.45"},
                json=report_json_data,
            )

            args = Namespace(
                report_id="1",
                path=json_file_path,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.SERVER_TOO_OLD_FOR_CLI % {
                    "min_version": MIN_SERVER_VERSION,
                    "current_version": "0.0.45",
                }
                assert err_msg in caplog.text


def test_list_report_as_json_no_output_file(
    caplog, capsys, requests_mock, get_report_url, report_json_data
):
    """Testing retrieving list report as json without output file."""
    caplog.set_level("INFO")
    requests_mock.get(
        get_report_url,
        status_code=200,
        json=report_json_data,
        headers={"X-Server-Version": VERSION},
    )
    sys.argv = [
        "/bin/qpc",
        "report",
        "list",
    ]
    CLI().main()
    assert caplog.messages[-1] == messages.REPORT_SUCCESSFULLY_WRITTEN
    captured = capsys.readouterr()
    assert json.loads(captured.out)
