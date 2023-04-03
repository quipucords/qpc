"""Test the CLI module."""

import sys
import unittest
from argparse import ArgumentParser, Namespace
from io import StringIO

import requests_mock

from qpc import messages
from qpc.release import PKG_NAME
from qpc.report import ASYNC_MERGE_URI
from qpc.report.merge_status import ReportMergeStatusCommand
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest="subcommand")


class ReportMergeStatusTests(unittest.TestCase):
    """Class for testing the report merge status commands for qpc."""

    # pylint: disable=invalid-name
    def setUp(self):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()
        self.url = get_server_location() + ASYNC_MERGE_URI

    def tearDown(self):
        """Remove test setup."""
        sys.stderr = self.orig_stderr

    def test_job_valid_id(self):
        """Test the job command with a vaild ID."""
        good_json = {
            "id": 1,
            "scan_type": "fingerprint",
            "status": "completed",
            "status_message": "Job is complete.",
            "tasks": [
                {
                    "scan_type": "fingerprint",
                    "status": "completed",
                    "status_message": "Task ran successfully",
                    "start_time": "time",
                    "end_time": "time",
                }
            ],
            "report_id": 10,
            "start_time": "time",
            "end_time": "time",
            "systems_fingerprint_count": 0,
        }

        with requests_mock.Mocker() as mocker:
            mocker.get(self.url + "1/", status_code=200, json=good_json)
            nac = ReportMergeStatusCommand(SUBPARSER)
            args = Namespace(job_id="1")
            with self.assertLogs(level="INFO") as log:
                nac.main(args)
                result1 = messages.MERGE_JOB_ID_STATUS % {
                    "job_id": "1", "status": "completed"
                }
                result2 = messages.DISPLAY_REPORT_ID % {
                    "report_id": "10",
                    "pkg_name": PKG_NAME,
                }
                self.assertIn(result1, log.output[-2])
                self.assertIn(result2, log.output[-1])

    def test_job_id_not_exist(self):
        """Test the job command with an invalid ID."""
        report_out = StringIO()
        with requests_mock.Mocker() as mocker:
            mocker.get(self.url + "1/", status_code=404, json=None)
            nac = ReportMergeStatusCommand(SUBPARSER)
            args = Namespace(job_id="1")
            with self.assertRaises(SystemExit):
                with redirect_stdout(report_out):
                    nac.main(args)
                    self.assertEqual(
                        report_out.getvalue(), messages.MERGE_JOB_ID_NOT_FOUND % "1"
                    )
