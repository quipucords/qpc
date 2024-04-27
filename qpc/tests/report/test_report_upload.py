"""Test the CLI module."""

import logging
from argparse import ArgumentParser, Namespace

import pytest
import requests_mock

from qpc import messages
from qpc.release import QPC_VAR_PROGRAM_NAME
from qpc.report import ASYNC_UPLOAD_URI
from qpc.report.upload import ReportUploadCommand
from qpc.utils import get_server_location

NONEXIST_FILE = "/tmp/does/not/exist/bad.json"


@pytest.fixture
def bad_details_report(tmp_path):
    """Return a malformatted report for testing."""
    report = tmp_path / "bad_details_report.json"
    report.write_text('{"id": 4,"bsources":[{"facts": ["A"],"server_id": "8"}]}')
    return str(report)


@pytest.fixture
def good_details_report(tmp_path):
    """Return a valid report for testing."""
    report = tmp_path / "good_details_report.json"
    report.write_text('{"id": 4,"sources":[{"facts": ["A"],"server_id": "8"}]}')
    return str(report)


@pytest.mark.usefixtures("server_config")
class TestReportUploadTests:
    """Class for testing the scan show commands for qpc."""

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = ReportUploadCommand(subparser)

    def test_upload_good_details_report(self, capsys, good_details_report):
        """Test uploading a good details report."""
        put_report_data = {"job_id": 1}
        put_merge_url = get_server_location() + ASYNC_UPLOAD_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(put_merge_url, status_code=201, json=put_report_data)
            args = Namespace(json_file=good_details_report)
            self.command.main(args)
            captured_output = capsys.readouterr()
            expected_message = messages.REPORT_SUCCESSFULLY_UPLOADED % {
                "id": "1",
                "prog_name": QPC_VAR_PROGRAM_NAME,
            }
            assert expected_message in captured_output.out

    def test_upload_bad_details_report(self, caplog, bad_details_report):
        """Test uploading a bad details report."""
        put_report_data = {"job_id": 1}
        put_merge_url = get_server_location() + ASYNC_UPLOAD_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(put_merge_url, status_code=201, json=put_report_data)

            args = Namespace(json_file=bad_details_report)
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_UPLOAD_FILE_INVALID_JSON % (
                    bad_details_report
                )
                assert err_msg in caplog.text

    def test_upload_bad_details_report_no_fingerprints(
        self, caplog, good_details_report
    ):
        """Test uploading a details report that produces no fingerprints."""
        put_report_data = {
            "error": "FAILED to create report id=23 - produced no valid fingerprints"
        }
        put_merge_url = get_server_location() + ASYNC_UPLOAD_URI
        with requests_mock.Mocker() as mocker:
            mocker.post(put_merge_url, status_code=400, json=put_report_data)

            args = Namespace(json_file=good_details_report)
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_FAILED_TO_UPLOADED % (
                    put_report_data.get("error")
                )
                assert err_msg in caplog.text
