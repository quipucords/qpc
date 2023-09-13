"""Test the CLI module."""

import json
import logging
import sys
import time
from argparse import ArgumentParser, Namespace
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
import requests_mock

from qpc import messages
from qpc.cli import CLI
from qpc.release import VERSION
from qpc.report import REPORT_URI
from qpc.report.details import ReportDetailsCommand
from qpc.scan import SCAN_JOB_URI
from qpc.tests_utilities import redirect_stdout
from qpc.utils import create_tar_buffer, get_server_location


@pytest.fixture
def json_file(tmp_path):
    """Return a fake json file."""
    return str(tmp_path / "test.json")


@pytest.fixture
def csv_file(tmp_path):
    """Return a fake csv file."""
    return str(tmp_path / "test.csv")


@pytest.mark.usefixtures("server_config")
class TestReportDetails:
    """Class for testing the details report command."""

    def _init_command(self):
        """Initialize command."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        return ReportDetailsCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        # different from most other test cases where command is initialized once per
        # class, this one requires to be initialized for each test method because
        # SourceEditCommand instance modifies req_path on the fly. This seems to be a
        # code smell to me, but I'm choosing to ignore it for now
        self.command = self._init_command()

    def test_detail_report_as_json(self, caplog, json_file):
        """Testing retrieving detail report as json."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {json_file: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200, json=get_scanjob_json_data)
            mocker.get(
                get_report_url,
                status_code=200,
                content=buffer_content,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                scan_job_id="1",
                report_id=None,
                output_json=True,
                output_csv=False,
                path=json_file,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.REPORT_SUCCESSFULLY_WRITTEN in caplog.text
                with Path(json_file).open("r", encoding="utf-8") as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                assert get_report_json_data == file_content_dict

    def test_detail_report_as_json_report_id(self, caplog, json_file):
        """Testing retrieving detail report as json with report id."""
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {json_file: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=200,
                content=buffer_content,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                output_json=True,
                output_csv=False,
                path=json_file,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.REPORT_SUCCESSFULLY_WRITTEN in caplog.text
                with Path(json_file).open("r", encoding="utf-8") as file_buffer:
                    data = file_buffer.read()
                    file_content_dict = json.loads(data)
                assert get_report_json_data == file_content_dict

    def test_detail_report_as_csv(self, caplog, csv_file):
        """Testing retrieving detail report as csv."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
        get_report_csv_data = "Report\n"
        get_report_csv_data += "1\n\n\n"
        get_report_csv_data += "key\n"
        get_report_csv_data += "value\n"

        get_report_csv_data = {"id": 1, "report": [{"key": "value"}]}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200, json=get_scanjob_json_data)
            mocker.get(
                get_report_url,
                status_code=200,
                json=get_report_csv_data,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                scan_job_id="1",
                report_id=None,
                output_json=False,
                output_csv=True,
                path=csv_file,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.REPORT_SUCCESSFULLY_WRITTEN in caplog.text
                with Path(csv_file).open("r", encoding="utf-8") as csv_buffer:
                    data = csv_buffer.read()
                    file_content_dict = json.loads(data)
                assert get_report_csv_data == file_content_dict

    # Test validation
    def test_detail_report_output_directory(self):
        """Testing fail because output directory."""
        with pytest.raises(SystemExit):
            sys.argv = ["/bin/qpc", "report", "detail", "--json", "--output-file", "/"]
            CLI().main()

    def test_detail_report_output_directory_not_exist(self):
        """Testing fail because output directory does not exist."""
        with pytest.raises(SystemExit):
            sys.argv = [
                "/bin/qpc",
                "report",
                "detail",
                "--json",
                "--output-file",
                "/foo/bar/",
            ]
            CLI().main()

    def test_detail_report_output_file_empty(self):
        """Testing fail because output file empty."""
        with pytest.raises(SystemExit):
            sys.argv = ["/bin/qpc", "report", "detail", "--json", "--output-file", ""]
            CLI().main()

    def test_detail_report_scan_job_not_exist(self, json_file):
        """Details report with nonexistent scanjob."""
        report_out = StringIO()

        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=400, json=get_scanjob_json_data)

            args = Namespace(
                scan_job_id="1",
                report_id=None,
                output_json=True,
                output_csv=False,
                path=json_file,
            )
            with pytest.raises(SystemExit):
                with redirect_stdout(report_out):
                    self.command.main(args)
                    assert report_out.getvalue() == messages.REPORT_SJ_DOES_NOT_EXIST

    def test_detail_report_invalid_scan_job(self, json_file):
        """Details report with scanjob but no report_id."""
        report_out = StringIO()

        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200, json=get_scanjob_json_data)

            args = Namespace(
                scan_job_id="1",
                report_id=None,
                output_json=True,
                output_csv=False,
                path=json_file,
            )
            with pytest.raises(SystemExit):
                with redirect_stdout(report_out):
                    self.command.main(args)
                    assert (
                        report_out.getvalue() == messages.REPORT_NO_DETAIL_REPORT_FOR_SJ
                    )

    @patch("qpc.report.details.write_file")
    def test_details_file_fails_to_write(self, file, caplog, json_file):
        """Testing details failure while writing to file."""
        file.side_effect = EnvironmentError()
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {json_file: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=200,
                content=buffer_content,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                output_json=True,
                output_csv=False,
                path=json_file,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.WRITE_FILE_ERROR % {
                    "path": json_file,
                    "error": "",
                }
                assert err_msg in caplog.text

    def test_details_nonexistent_directory(self, caplog, json_file):
        """Testing error for nonexistent directory in output."""
        fake_dir = "/cody/is/awesome/details.json"
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {json_file: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200, content=buffer_content)

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                output_json=True,
                output_csv=False,
                path=fake_dir,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = (
                    messages.REPORT_DIRECTORY_DOES_NOT_EXIST % Path(fake_dir).parent
                )
                assert err_msg in caplog.text

    def test_details_nonjson_path(self, caplog, json_file):
        """Testing error for non json file path."""
        non_json_dir = "/Users/details.tar.gz"
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {json_file: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200, content=buffer_content)

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                output_json=True,
                output_csv=False,
                path=non_json_dir,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.OUTPUT_FILE_TYPE % ".json"
                assert err_msg in caplog.text

    def test_details_noncsv_path(self, caplog, json_file):
        """Testing error for noncsv file path."""
        non_csv_dir = "/Users/details.tar.gz"
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {json_file: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200, content=buffer_content)

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                output_json=False,
                output_csv=True,
                path=non_csv_dir,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.OUTPUT_FILE_TYPE % ".csv"
                assert err_msg in caplog.text

    def test_details_report_id_not_exist(self, caplog, json_file):
        """Test details with nonexistent report id."""
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=400,
                json=get_report_json_data,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                output_json=True,
                output_csv=False,
                path=json_file,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_NO_DETAIL_REPORT_FOR_REPORT_ID % 1
                assert err_msg in caplog.text

    def test_detail_report_error_scan_job(self, caplog, json_file):
        """Testing error with scan job id."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {json_file: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200, json=get_scanjob_json_data)
            mocker.get(
                get_report_url,
                status_code=400,
                content=buffer_content,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                scan_job_id="1",
                report_id=None,
                output_json=True,
                output_csv=False,
                path=json_file,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_NO_DETAIL_REPORT_FOR_SJ % 1
                assert err_msg in caplog.text

    def test_details_old_version(self, caplog, csv_file):
        """Test too old server version."""
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=400,
                headers={"X-Server-Version": "0.0.45"},
                json=get_report_json_data,
            )

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                output_json=False,
                output_csv=True,
                path=csv_file,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.SERVER_TOO_OLD_FOR_CLI % {
                    "min_version": "0.9.2",
                    "current_version": "0.0.45",
                }
                assert err_msg in caplog.text


def test_details_report_as_json_no_output_file(caplog, capsys, requests_mock):
    """Testing retrieving details report as json without output file."""
    caplog.set_level("INFO")
    report_url = get_server_location() + REPORT_URI + "1/details/"
    report_json_data = {"id": 1, "report": [{"key": "value"}]}
    json_filename = f"test_{time.time():.0f}.json"
    buffer_content = create_tar_buffer({json_filename: report_json_data})

    requests_mock.get(
        report_url,
        status_code=200,
        content=buffer_content,
        headers={"X-Server-Version": VERSION},
    )
    sys.argv = [
        "/bin/qpc",
        "report",
        "details",
        "--json",
        "--report",
        "1",
    ]
    CLI().main()
    assert caplog.messages[-1] == messages.REPORT_SUCCESSFULLY_WRITTEN
    captured = capsys.readouterr()
    assert json.loads(captured.out)
