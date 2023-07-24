"""Test the CLI module."""

import json
import logging
import os
import sys
import time
from argparse import ArgumentParser, Namespace  # noqa: I100
from io import StringIO  # noqa: I100
from unittest.mock import patch

import pytest
import requests_mock

from qpc import messages
from qpc.cli import CLI
from qpc.release import VERSION
from qpc.report import REPORT_URI
from qpc.report.deployments import ReportDeploymentsCommand
from qpc.scan import SCAN_JOB_URI
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import create_tar_buffer, get_server_location, write_server_config


class TestReportDeployments:
    """Class for testing the deployments report command."""

    def _init_command(self):
        """Initialize command."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        return ReportDeploymentsCommand(subparser)

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
        self.test_json_filename = f"test_{time.time():.0f}.json"
        self.test_csv_filename = f"test_{time.time():.0f}.csv"
        sys.stderr = HushUpStderr()

    def teardown_method(self, _test_method):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr
        try:
            os.remove(self.test_json_filename)
        except FileNotFoundError:
            pass
        try:
            os.remove(self.test_csv_filename)
        except FileNotFoundError:
            pass

    def test_deployments_report_as_json(self, caplog):
        """Testing retrieving deployments report as json."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        get_report_url = get_server_location() + REPORT_URI + "1/deployments/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_json_filename: get_report_json_data}
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
                path=self.test_json_filename,
                mask=False,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.REPORT_SUCCESSFULLY_WRITTEN in caplog.text
                with open(self.test_json_filename, "r", encoding="utf-8") as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                assert get_report_json_data == file_content_dict

    def test_deployments_report_as_json_report_id(self, caplog):
        """Testing retrieving deployments report as json with report id."""
        get_report_url = get_server_location() + REPORT_URI + "1/deployments/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_json_filename: get_report_json_data}
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
                path=self.test_json_filename,
                mask=False,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.REPORT_SUCCESSFULLY_WRITTEN in caplog.text
                with open(self.test_json_filename, "r", encoding="utf-8") as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                assert get_report_json_data == file_content_dict

    def test_deployments_report_as_csv(self, caplog):
        """Testing retreiving deployments report as csv."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        get_report_url = get_server_location() + REPORT_URI + "1/deployments/"
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
                path=self.test_csv_filename,
                mask=False,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.REPORT_SUCCESSFULLY_WRITTEN in caplog.text
                with open(self.test_csv_filename, "r", encoding="utf-8") as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                assert get_report_csv_data == file_content_dict

    # Test validation
    def test_deployments_report_output_directory(self):
        """Testing fail because output directory."""
        with pytest.raises(SystemExit):
            sys.argv = [
                "/bin/qpc",
                "report",
                "deployments",
                "--json",
                "--output-file",
                "/",
            ]
            CLI().main()

    def test_deployments_report_output_directory_not_exist(self):
        """Testing fail because output directory does not exist."""
        with pytest.raises(SystemExit):
            sys.argv = [
                "/bin/qpc",
                "report",
                "deployments",
                "--json",
                "--output-file",
                "/foo/bar/",
            ]
            CLI().main()

    def test_deployments_report_output_file_empty(self):
        """Testing fail because output file empty."""
        with pytest.raises(SystemExit):
            sys.argv = [
                "/bin/qpc",
                "report",
                "deployments",
                "--json",
                "--output-file",
                "",
            ]
            CLI().main()

    def test_deployments_report_scan_job_not_exist(self):
        """Deployments report with nonexistent scanjob."""
        report_out = StringIO()

        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=400, json=get_scanjob_json_data)

            args = Namespace(
                scan_job_id="1",
                output_json=True,
                report_id=None,
                output_csv=False,
                path=self.test_json_filename,
                mask=False,
            )
            with pytest.raises(SystemExit):
                with redirect_stdout(report_out):
                    self.command.main(args)
                    assert report_out.getvalue() == messages.REPORT_SJ_DOES_NOT_EXIST

    def test_deployments_report_invalid_scan_job(self):
        """Deployments report with scanjob but no report_id."""
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
                path=self.test_json_filename,
                mask=False,
            )
            with pytest.raises(SystemExit):
                with redirect_stdout(report_out):
                    self.command.main(args)
                    assert (
                        report_out.getvalue()
                        == messages.REPORT_NO_DEPLOYMENTS_REPORT_FOR_SJ
                    )

    @patch("qpc.report.deployments.write_file")
    def test_deployments_file_fails_to_write(self, file, caplog):
        """Testing deployments failure while writing to file."""
        file.side_effect = EnvironmentError()
        get_report_url = get_server_location() + REPORT_URI + "1/deployments/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_json_filename: get_report_json_data}
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
                path=self.test_json_filename,
                mask=False,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.WRITE_FILE_ERROR % {
                    "path": self.test_json_filename,
                    "error": "",
                }
                assert err_msg in caplog.text

    def test_deployments_nonexistent_directory(self, caplog):
        """Testing error for nonexistent directory in output."""
        fake_dir = "/cody/is/awesome/deployments.json"
        get_report_url = get_server_location() + REPORT_URI + "1/deployments/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_json_filename: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200, content=buffer_content)

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                output_json=True,
                output_csv=False,
                path=fake_dir,
                mask=False,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_DIRECTORY_DOES_NOT_EXIST % os.path.dirname(
                    fake_dir
                )
                assert err_msg in caplog.text

    def test_deployments_nonjson_directory(self, caplog):
        """Testing error for nonjson output path."""
        non_json_dir = "/Users/deployments.tar.gz"
        get_report_url = get_server_location() + REPORT_URI + "1/deployments/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_json_filename: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200, content=buffer_content)

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                output_json=True,
                output_csv=False,
                path=non_json_dir,
                mask=False,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.OUTPUT_FILE_TYPE % ".json"
                assert err_msg in caplog.text

    def test_deployments_noncsv_directory(self, caplog):
        """Testing error for noncsv output path."""
        non_csv_dir = "/cody/is/awesome/deployments.tar.gz"
        get_report_url = get_server_location() + REPORT_URI + "1/deployments/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_json_filename: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200, content=buffer_content)

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                output_json=False,
                output_csv=True,
                path=non_csv_dir,
                mask=False,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.OUTPUT_FILE_TYPE % ".csv"
                assert err_msg in caplog.text

    def test_deployments_report_id_not_exist(self, caplog):
        """Test deployments with nonexistent report id."""
        get_report_url = get_server_location() + REPORT_URI + "1/deployments/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_json_filename: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=400,
                content=buffer_content,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                output_json=True,
                output_csv=False,
                path=self.test_json_filename,
                mask=False,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_NO_DEPLOYMENTS_REPORT_FOR_REPORT_ID % 1
                assert err_msg in caplog.text

    def test_deployments_report_error_scan_job(self, caplog):
        """Testing error with scan job id."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        get_report_url = get_server_location() + REPORT_URI + "1/deployments/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_json_filename: get_report_json_data}
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
                path=self.test_json_filename,
                mask=False,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_NO_DEPLOYMENTS_REPORT_FOR_SJ % 1
                assert err_msg in caplog.text

    def test_deployments_report_mask(self, caplog):
        """Testing retrieving json deployments report with masked values."""
        get_report_url = (
            get_server_location() + REPORT_URI + "1/deployments/" + "?mask=True"
        )
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_json_filename: get_report_json_data}
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
                path=self.test_json_filename,
                mask=True,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.REPORT_SUCCESSFULLY_WRITTEN in caplog.text
                with open(self.test_json_filename, "r", encoding="utf-8") as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                assert get_report_json_data == file_content_dict

    def test_deployments_masked_sj_428(self, caplog):
        """Deployments report retrieved from sj returns 428."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        get_report_url = get_server_location() + REPORT_URI + "1/deployments/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_json_filename: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200, json=get_scanjob_json_data)
            mocker.get(
                get_report_url,
                status_code=428,
                content=buffer_content,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                scan_job_id="1",
                report_id=None,
                output_json=True,
                output_csv=False,
                path=self.test_json_filename,
                mask=True,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_COULD_NOT_BE_MASKED_SJ % 1
                assert err_msg in caplog.text

    def test_deployments_masked_report_428(self, caplog):
        """Deployments report retrieved from report returns 428."""
        get_report_url = (
            get_server_location() + REPORT_URI + "1/deployments/" + "?mask=True"
        )
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_json_filename: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=428,
                content=buffer_content,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                scan_job_id=None,
                report_id="1",
                output_json=True,
                output_csv=False,
                path=self.test_json_filename,
                mask=True,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_COULD_NOT_BE_MASKED_REPORT_ID % 1
                assert err_msg in caplog.text

    def test_deployments_old_version(self, caplog):
        """Test too old server version."""
        get_report_url = get_server_location() + REPORT_URI + "1/deployments/"
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
                output_json=True,
                output_csv=False,
                path=self.test_json_filename,
                mask=False,
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.SERVER_TOO_OLD_FOR_CLI % {
                    "min_version": "0.9.2",
                    "current_version": "0.0.45",
                }
                assert err_msg in caplog.text


def test_deployments_report_as_json_no_output_file(caplog, capsys, requests_mock):
    """Testing retrieving deployments report as json without output file."""
    caplog.set_level("INFO")
    report_url = get_server_location() + REPORT_URI + "1/deployments/"
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
        "deployments",
        "--json",
        "--report",
        "1",
    ]
    CLI().main()
    assert messages.REPORT_SUCCESSFULLY_WRITTEN in caplog.text
    captured = capsys.readouterr()
    assert json.loads(captured.out)