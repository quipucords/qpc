"""Test the CLI report show subcommand."""

import json
import logging
import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest
import requests_mock

from qpc import messages
from qpc.cli import CLI
from qpc.release import VERSION
from qpc.report import REPORT_V2_URI
from qpc.report.show import ReportShowCommand
from qpc.tests.utilities import redirect_stdout
from qpc.utils import get_server_location


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

    def test_show_report_as_json_to_stdout(self, get_report1_url, report1_json_data):
        """Testing report show is sent as json to stdout."""
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report1_url,
                status_code=200,
                json=report1_json_data,
                headers={"X-Server-Version": VERSION},
            )

            args = Namespace(
                report_id=1,
            )
            report_out = StringIO()
            with redirect_stdout(report_out):
                self.command.main(args)
                assert json.loads(report_out.getvalue()) == report1_json_data

    # Test validation

    def test_show_report_id_not_exist(self, caplog, get_report1_url, report1_json_data):
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
            )
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_ID_DOES_NOT_EXIST % 1
                assert err_msg in caplog.text


def test_show_report_as_json(
    caplog, capsys, requests_mock, get_report1_url, report1_json_data
):
    """Testing show report is json."""
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
    captured = capsys.readouterr()
    assert json.loads(captured.out)
