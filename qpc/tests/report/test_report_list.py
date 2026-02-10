"""Test the CLI report list subcommand."""

import json
import logging
import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest
import requests_mock

from qpc import messages
from qpc.cli import CLI
from qpc.report import REPORT_V2_URI
from qpc.report.list import MIN_SERVER_VERSION, ReportListCommand
from qpc.tests.utilities import redirect_stdout
from qpc.utils import get_server_location

VERSION = MIN_SERVER_VERSION


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

    def test_list_report_as_json_to_stdout(self, get_report_url, report_json_data):
        """Testing retrieving the list of reports as json to stdout."""
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=200,
                json=report_json_data,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace()
            report_out = StringIO()
            with redirect_stdout(report_out):
                self.command.main(args)
                assert json.loads(report_out.getvalue()) == report_json_data

    # Test validation

    def test_list_old_version(self, caplog, get_report_url, report_json_data):
        """Test server version is too old."""
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=400,
                headers={"X-Server-Version": "0.0.45"},
                json=report_json_data,
            )

            args = Namespace()
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.SERVER_TOO_OLD_FOR_CLI % {
                    "min_version": MIN_SERVER_VERSION,
                    "current_version": "0.0.45",
                }
                assert err_msg in caplog.text


def test_list_report_as_json(
    caplog, capsys, requests_mock, get_report_url, report_json_data
):
    """Testing retrieving list report is a json."""
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
    captured = capsys.readouterr()
    assert json.loads(captured.out)
