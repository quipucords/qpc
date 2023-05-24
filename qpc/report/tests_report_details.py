"""Test the CLI module."""

import json
import os
import sys
import time
import unittest
from argparse import ArgumentParser, Namespace  # noqa: I100
from io import StringIO  # noqa: I100
from unittest.mock import patch

import requests_mock

from qpc import messages
from qpc.cli import CLI
from qpc.release import VERSION
from qpc.report import REPORT_URI
from qpc.report.details import ReportDetailsCommand
from qpc.scan import SCAN_JOB_URI
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import create_tar_buffer, get_server_location, write_server_config


class ReportDetailsTests(unittest.TestCase):
    """Class for testing the details report command."""

    def _init_command(self):
        """Initialize command."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        return ReportDetailsCommand(subparser)

    def setUp(self):  # pylint: disable=invalid-name
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

    def tearDown(self):
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

    def test_detail_report_as_json(self):
        """Testing retrieving detail report as json."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
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
            with self.assertLogs(level="INFO") as log:
                self.command.main(args)
                self.assertIn(messages.REPORT_SUCCESSFULLY_WRITTEN, log.output[-1])
                with open(self.test_json_filename, "r", encoding="utf-8") as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                self.assertDictEqual(get_report_json_data, file_content_dict)

    def test_detail_report_as_json_report_id(self):
        """Testing retrieving detail report as json with report id."""
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
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
            with self.assertLogs(level="INFO") as log:
                self.command.main(args)
                self.assertIn(messages.REPORT_SUCCESSFULLY_WRITTEN, log.output[-1])
                with open(self.test_json_filename, "r", encoding="utf-8") as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                self.assertDictEqual(get_report_json_data, file_content_dict)

    def test_detail_report_as_csv(self):
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
                path=self.test_csv_filename,
                mask=False,
            )
            with self.assertLogs(level="INFO") as log:
                self.command.main(args)
                self.assertIn(messages.REPORT_SUCCESSFULLY_WRITTEN, log.output[-1])
                with open(self.test_csv_filename, "r", encoding="utf-8") as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                self.assertDictEqual(get_report_csv_data, file_content_dict)

    # Test validation
    def test_detail_report_output_directory(self):
        """Testing fail because output directory."""
        with self.assertRaises(SystemExit):
            sys.argv = ["/bin/qpc", "report", "detail", "--json", "--output-file", "/"]
            CLI().main()

    def test_detail_report_output_directory_not_exist(self):
        """Testing fail because output directory does not exist."""
        with self.assertRaises(SystemExit):
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
        with self.assertRaises(SystemExit):
            sys.argv = ["/bin/qpc", "report", "detail", "--json", "--output-file", ""]
            CLI().main()

    def test_detail_report_scan_job_not_exist(self):
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
                path=self.test_json_filename,
                mask=False,
            )
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    self.command.main(args)
                    self.assertEqual(
                        report_out.getvalue(), messages.REPORT_SJ_DOES_NOT_EXIST
                    )

    def test_detail_report_invalid_scan_job(self):
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
                path=self.test_json_filename,
                mask=False,
            )
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    self.command.main(args)
                    self.assertEqual(
                        report_out.getvalue(), messages.REPORT_NO_DETAIL_REPORT_FOR_SJ
                    )

    @patch("qpc.report.details.write_file")
    def test_details_file_fails_to_write(self, file):
        """Testing details failure while writing to file."""
        file.side_effect = EnvironmentError()
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
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
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    self.command.main(args)
                err_msg = messages.WRITE_FILE_ERROR % {
                    "path": self.test_json_filename,
                    "error": "",
                }
                self.assertIn(err_msg, log.output[0])

    def test_details_nonexistent_directory(self):
        """Testing error for nonexistent directory in output."""
        fake_dir = "/cody/is/awesome/details.json"
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
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
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_DIRECTORY_DOES_NOT_EXIST % os.path.dirname(
                    fake_dir
                )
                self.assertIn(err_msg, log.output[0])

    def test_details_nonjson_path(self):
        """Testing error for non json file path."""
        non_json_dir = "/Users/details.tar.gz"
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
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
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    self.command.main(args)
                err_msg = messages.OUTPUT_FILE_TYPE % ".json"
                self.assertIn(err_msg, log.output[0])

    def test_details_noncsv_path(self):
        """Testing error for noncsv file path."""
        non_csv_dir = "/Users/details.tar.gz"
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
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
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    self.command.main(args)
                err_msg = messages.OUTPUT_FILE_TYPE % ".csv"
                self.assertIn(err_msg, log.output[0])

    def test_details_report_id_not_exist(self):
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
                path=self.test_json_filename,
                mask=False,
            )
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_NO_DETAIL_REPORT_FOR_REPORT_ID % 1
                self.assertIn(err_msg, log.output[0])

    def test_detail_report_error_scan_job(self):
        """Testing error with scan job id."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        get_report_url = get_server_location() + REPORT_URI + "1/details/"
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
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_NO_DETAIL_REPORT_FOR_SJ % 1
                self.assertIn(err_msg, log.output[0])

    def test_detail_report_as_csv_masked(self):
        """Testing retrieving csv details report with masked query param."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        get_report_url = (
            get_server_location() + REPORT_URI + "1/details/" + "?mask=True"
        )
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
                mask=True,
            )
            with self.assertLogs(level="INFO") as log:
                self.command.main(args)
                self.assertIn(messages.REPORT_SUCCESSFULLY_WRITTEN, log.output[-1])
                with open(self.test_csv_filename, "r", encoding="utf-8") as json_file:
                    data = json_file.read()
                    file_content_dict = json.loads(data)
                self.assertDictEqual(get_report_csv_data, file_content_dict)

    def test_details_old_version(self):
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
                path=self.test_csv_filename,
                mask=False,
            )
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    self.command.main(args)
                err_msg = messages.SERVER_TOO_OLD_FOR_CLI % {
                    "min_version": "0.9.2",
                    "current_version": "0.0.45",
                }
                self.assertIn(err_msg, log.output[0])


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
