"""Test the CLI report show subcommand."""

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
from qpc.report.show import MIN_SERVER_VERSION, ReportShowCommand
from qpc.utils import get_server_location

VERSION = MIN_SERVER_VERSION


@pytest.fixture
def json_file_path(tmp_path) -> str:
    """Return a fake json file path string."""
    return str(tmp_path / "test.json")


@pytest.fixture
def get_report1_url() -> str:
    """Return a get report url for report 1."""
    return get_server_location() + REPORT_V2_URI + "1/"


@pytest.fixture
def report1_json_data() -> dict:
    """Return a fake report json data."""
    return {"id": 1, "can_publish": True, "origin": "local"}


@pytest.mark.usefixtures("server_config")
class TestReportShowCommand:
    """Class for testing the show report command."""

    def _init_command(self):
        """Initialize command."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        return ReportShowCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        self.command = self._init_command()

    def test_show_report_as_json(
        self, caplog, json_file_path, get_report1_url, report1_json_data
    ):
        """Testing retrieving report as json."""
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report1_url,
                status_code=200,
                json=report1_json_data,
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
                assert report1_json_data == file_content_dict

    # Test validation
    def test_show_report_output_directory(self):
        """Testing fail because output directory."""
        with pytest.raises(SystemExit):
            sys.argv = [
                "/bin/qpc",
                "report",
                "show",
                "--report",
                "1",
                "--output-file",
                "/",
            ]
            CLI().main()

    def test_show_report_output_directory_not_exist(self):
        """Testing fail because output directory does not exist."""
        with pytest.raises(SystemExit):
            sys.argv = [
                "/bin/qpc",
                "report",
                "show",
                "--report",
                "1",
                "--output-file",
                "/foo/bar/",
            ]
            CLI().main()

    def test_show_report_output_file_empty(self):
        """Testing fail because output file empty."""
        with pytest.raises(SystemExit):
            sys.argv = [
                "/bin/qpc",
                "report",
                "show",
                "--report",
                "1",
                "--output-file",
                "",
            ]
            CLI().main()

    @patch("qpc.report.show.write_file")
    def test_show_file_fails_to_write(
        self, file, caplog, json_file_path, get_report1_url, report1_json_data
    ):
        """Testing show failure while writing to file."""
        file.side_effect = EnvironmentError()
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report1_url,
                status_code=200,
                json=report1_json_data,
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

    def test_show_nonexistent_directory(
        self, caplog, json_file_path, get_report1_url, report1_json_data
    ):
        """Testing error for nonexistent directory in output."""
        fake_dir = "/cody/is/awesome/show.json"
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report1_url, status_code=200, json=report1_json_data)

            args = Namespace(
                report_id="1",
                path=fake_dir,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = (
                    messages.REPORT_DIRECTORY_DOES_NOT_EXIST % Path(fake_dir).parent
                )
                assert err_msg in caplog.text

    def test_show_non_json_path(
        self, caplog, json_file_path, get_report1_url, report1_json_data
    ):
        """Testing error for non json file path."""
        non_json_dir = "/Users/show.tar.gz"
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report1_url, status_code=200, json=report1_json_data)

            args = Namespace(
                report_id="1",
                path=non_json_dir,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.OUTPUT_FILE_TYPE % ".json"
                assert err_msg in caplog.text

    def test_show_report_id_not_exist(
        self, caplog, json_file_path, get_report1_url, report1_json_data
    ):
        """Test show with nonexistent report id."""
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report1_url,
                status_code=400,
                json=report1_json_data,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                report_id="1",
                path=json_file_path,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_ID_DOES_NOT_EXIST % 1
                assert err_msg in caplog.text

    def test_show_old_version(
        self, caplog, json_file_path, get_report1_url, report1_json_data
    ):
        """Test too old server version."""
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report1_url,
                status_code=400,
                headers={"X-Server-Version": "0.0.45"},
                json=report1_json_data,
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


def test_show_report_as_json_no_output_file(
    caplog, capsys, requests_mock, get_report1_url, report1_json_data
):
    """Testing retrieving show report as json without output file."""
    caplog.set_level("INFO")
    requests_mock.get(
        get_report1_url,
        status_code=200,
        json=report1_json_data,
        headers={"X-Server-Version": VERSION},
    )
    sys.argv = [
        "/bin/qpc",
        "report",
        "show",
        "--report",
        "1",
    ]
    CLI().main()
    assert caplog.messages[-1] == messages.REPORT_SUCCESSFULLY_WRITTEN
    captured = capsys.readouterr()
    assert json.loads(captured.out)
