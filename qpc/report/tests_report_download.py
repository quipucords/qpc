"""Test the CLI module."""

import os
import sys
import time
import unittest
from argparse import ArgumentParser, Namespace  # noqa: I100
from unittest.mock import patch

import requests_mock

from qpc import messages
from qpc.cli import CLI
from qpc.release import VERSION
from qpc.report import REPORT_URI
from qpc.report.download import ReportDownloadCommand
from qpc.scan import SCAN_JOB_URI
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr
from qpc.utils import create_tar_buffer, get_server_location, write_server_config

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest="subcommand")


class ReportDownloadTests(unittest.TestCase):
    """Class for testing the report download command."""

    # pylint: disable=invalid-name
    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        self.test_tar_filename = f"test_{time.time():.0f}.tar.gz"
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Remove test setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr
        try:
            os.remove(self.test_tar_filename)
        except FileNotFoundError:
            pass

    def test_download_scan_job(self):
        """Testing download with scan job id."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        get_report_url = get_server_location() + REPORT_URI + "1"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {"test.json": get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)

        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200, json=get_scanjob_json_data)
            mocker.get(
                get_report_url,
                status_code=200,
                headers={"X-Server-Version": VERSION},
                content=buffer_content,
            )
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(
                scan_job_id="1", report_id=None, path=self.test_tar_filename, mask=False
            )
            with self.assertLogs(level="INFO") as log:
                nac.main(args)
                expected_msg = messages.DOWNLOAD_SUCCESSFULLY_WRITTEN % {
                    "report": "1",
                    "path": self.test_tar_filename,
                }
                self.assertIn(expected_msg, log.output[-1])

    def test_download_report_id(self):
        """Testing download with report id."""
        get_report_url = get_server_location() + REPORT_URI + "1"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_tar_filename: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=200,
                headers={"X-Server-Version": VERSION},
                content=buffer_content,
            )
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(
                scan_job_id=None, report_id="1", path=self.test_tar_filename, mask=False
            )
            with self.assertLogs(level="INFO") as log:
                nac.main(args)
                expected_msg = messages.DOWNLOAD_SUCCESSFULLY_WRITTEN % {
                    "report": "1",
                    "path": self.test_tar_filename,
                }
                self.assertIn(expected_msg, log.output[-1])

    def test_download_output_directory(self):
        """Testing fail because of output directory."""
        with self.assertRaises(SystemExit):
            sys.argv = ["/bin/qpc", "report", "download", "--output-file", "/foo/bar"]
            CLI().main()

    def test_download_output_directory_not_exist(self):
        """Testing fail because output directory does not exist."""
        with self.assertRaises(SystemExit):
            sys.argv = ["/bin/qpc", "report", "download", "--output-file", "/foo/bar/"]
            CLI().main()

    def test_download_output_file_empty(self):
        """Testing fail because output file empty."""
        with self.assertRaises(SystemExit):
            sys.argv = ["/bin/qpc", "report", "download", "--output-file", ""]
            CLI().main()

    def test_download_report_empty(self):
        """Testing fail because output file empty."""
        with self.assertRaises(SystemExit):
            sys.argv = [
                "/bin/qpc",
                "report",
                "download",
                "--report",
                "",
                "--output-file",
                "test.json",
            ]
            CLI().main()

    def test_download_scan_job_not_exist(self):
        """Testing download with nonexistent scanjob."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=400, json=get_scanjob_json_data)
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(
                scan_job_id="1", report_id=None, path=self.test_tar_filename, mask=False
            )
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    nac.main(args)
                err_msg = messages.DOWNLOAD_SJ_DOES_NOT_EXIST % 1
                self.assertIn(err_msg, log.output[0])

    def test_download_invalid_scan_job(self):
        """Testing download with scanjob but no report_id."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200, json=get_scanjob_json_data)
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(
                scan_job_id="1", report_id=None, path=self.test_tar_filename, mask=False
            )
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    nac.main(args)
                err_msg = messages.DOWNLOAD_NO_REPORT_FOR_SJ % "1"
                self.assertIn(err_msg, log.output[0])

    def test_output_is_nonexistent_directory(self):
        """Testing error for nonexistent directory in output."""
        fake_dir = "/cody/is/awesome/"
        get_report_url = get_server_location() + REPORT_URI + "1"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_tar_filename: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200, content=buffer_content)
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(scan_job_id=None, report_id="1", path=fake_dir, mask=False)
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    nac.main(args)
                err_msg = messages.REPORT_DIRECTORY_DOES_NOT_EXIST % os.path.dirname(
                    fake_dir
                )
                self.assertIn(err_msg, log.output[0])

    @patch("qpc.report.download.write_file")
    def test_file_fails_to_write(self, file):
        """Testing download failure while writing to file."""
        err = "Mock Fail"
        file.side_effect = OSError(err)
        get_report_url = get_server_location() + REPORT_URI + "1"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_tar_filename: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=200,
                headers={"X-Server-Version": VERSION},
                content=buffer_content,
            )
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(
                scan_job_id=None, report_id="1", path=self.test_tar_filename, mask=False
            )
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    nac.main(args)
                err_msg = messages.WRITE_FILE_ERROR % {
                    "path": self.test_tar_filename,
                    "error": err,
                }
                self.assertIn(err_msg, log.output[0])

    def test_download_report_id_not_exist(self):
        """Test download with nonexistent report id."""
        get_report_url = get_server_location() + REPORT_URI + "1"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=400,
                headers={"X-Server-Version": VERSION},
                json=get_report_json_data,
            )
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(
                scan_job_id=None, report_id=1, path=self.test_tar_filename, mask=False
            )
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    nac.main(args)
                err_msg = messages.DOWNLOAD_NO_REPORT_FOUND % 1
                self.assertIn(err_msg, log.output[0])

    def test_download_from_server_with_old_version(self):
        """Test download with nonexistent report id."""
        get_report_url = get_server_location() + REPORT_URI + "1"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=400,
                headers={"X-Server-Version": "0.0.45"},
                json=get_report_json_data,
            )
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(
                scan_job_id=None, report_id=1, path=self.test_tar_filename, mask=False
            )
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    nac.main(args)
                err_msg = messages.SERVER_TOO_OLD_FOR_CLI % {
                    "min_version": "0.9.2",
                    "current_version": "0.0.45",
                }
                self.assertIn(err_msg, log.output[-1])

    def test_download_bad_file_extension(self):
        """Test download with bad file extension."""
        get_report_url = get_server_location() + REPORT_URI + "1"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_tar_filename: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=200,
                headers={"X-Server-Version": VERSION},
                content=buffer_content,
            )
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(
                scan_job_id=None, report_id="1", path="test.json", mask=False
            )
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    nac.main(args)
                err_msg = messages.OUTPUT_FILE_TYPE % "tar.gz"
                self.assertIn(err_msg, log.output[-1])

    def test_download_report_id_masked(self):
        """Testing download with report id and mask set to true."""
        get_report_url = get_server_location() + REPORT_URI + "1" + "?mask=True"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {self.test_tar_filename: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=200,
                headers={"X-Server-Version": VERSION},
                content=buffer_content,
            )
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(
                scan_job_id=None, report_id="1", path=self.test_tar_filename, mask=True
            )
            with self.assertLogs(level="INFO") as log:
                nac.main(args)
                expected_msg = messages.DOWNLOAD_SUCCESSFULLY_WRITTEN % {
                    "report": "1",
                    "path": self.test_tar_filename,
                }
                self.assertIn(expected_msg, log.output[-1])

    def test_download_report_id_428(self):
        """Test download with nonexistent report id."""
        get_report_url = get_server_location() + REPORT_URI + "1"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=428,
                headers={"X-Server-Version": VERSION},
                json=get_report_json_data,
            )
            nac = ReportDownloadCommand(SUBPARSER)
            args = Namespace(
                scan_job_id=None, report_id="1", path=self.test_tar_filename, mask=False
            )
            with self.assertLogs(level="ERROR") as log:
                with self.assertRaises(SystemExit):
                    nac.main(args)
                err_msg = messages.DOWNLOAD_NO_MASK_REPORT % 1
                self.assertIn(err_msg, log.output[0])
