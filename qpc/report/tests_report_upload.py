"""Test the CLI module."""

import logging
import os
import sys
from argparse import ArgumentParser, Namespace

import pytest
import requests_mock

from qpc import messages
from qpc.release import QPC_VAR_PROGRAM_NAME
from qpc.report import ASYNC_MERGE_URI
from qpc.report.upload import ReportUploadCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr
from qpc.utils import get_server_location, write_server_config

TMP_BADDETAILS1 = (
    "/tmp/testbaddetailsreport_source.json",
    '{"id": 4,"bsources":[{"facts": ["A"],"server_id": "8"}]}',
)
TMP_GOODDETAILS = (
    "/tmp/testgooddetailsreport.json",
    '{"id": 4,"sources":[{"facts": ["A"],"server_id": "8"}]}',
)
NONEXIST_FILE = "/tmp/does/not/exist/bad.json"
JSON_FILES_LIST = [TMP_BADDETAILS1, TMP_GOODDETAILS]


class TestReportUploadTests:
    """Class for testing the scan show commands for qpc."""

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = ReportUploadCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()
        for file in JSON_FILES_LIST:
            if os.path.isfile(file[0]):
                os.remove(file[0])
            with open(file[0], "w", encoding="utf-8") as test_file:
                test_file.write(file[1])

    def teardown_method(self, _test_method):
        """Remove test setup."""
        # Restore stderr
        for file in JSON_FILES_LIST:
            if os.path.isfile(file[0]):
                os.remove(file[0])
        sys.stderr = self.orig_stderr

    def test_upload_good_details_report(self, caplog):
        """Test uploading a good details report."""
        put_report_data = {"id": 1}
        put_merge_url = get_server_location() + ASYNC_MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(put_merge_url, status_code=201, json=put_report_data)

            args = Namespace(json_file=TMP_GOODDETAILS[0])
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.REPORT_SUCCESSFULLY_UPLOADED % {
                    "id": "1",
                    "prog_name": QPC_VAR_PROGRAM_NAME,
                }

                assert expected_message in caplog.text

    def test_upload_bad_details_report(self, caplog):
        """Test uploading a bad details report."""
        put_report_data = {"id": 1}
        put_merge_url = get_server_location() + ASYNC_MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(put_merge_url, status_code=201, json=put_report_data)

            args = Namespace(json_file=TMP_BADDETAILS1[0])
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_UPLOAD_FILE_INVALID_JSON % (
                    TMP_BADDETAILS1[0]
                )
                assert err_msg in caplog.text

    def test_upload_bad_details_report_no_fingerprints(self, caplog):
        """Test uploading a details report that produces no fingerprints."""
        put_report_data = {
            "error": "FAILED to create report id=23 - produced no valid fingerprints"
        }
        put_merge_url = get_server_location() + ASYNC_MERGE_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(put_merge_url, status_code=400, json=put_report_data)

            args = Namespace(json_file=TMP_GOODDETAILS[0])
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_FAILED_TO_UPLOADED % (
                    put_report_data.get("error")
                )
                assert err_msg in caplog.text
