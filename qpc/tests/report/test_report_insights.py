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
from qpc.report.insights import ReportInsightsCommand
from qpc.scan import SCAN_JOB_URI, SCAN_JOB_V2_URI
from qpc.tests.utilities import redirect_stdout
from qpc.utils import create_tar_buffer, get_server_location


@pytest.fixture
def fake_tarball(tmp_path):
    """Return a fake tarball."""
    return str(tmp_path / "test.tar.gz")


@pytest.mark.usefixtures("server_config")
class TestReportInsights:
    """Class for testing the insights report command."""

    def _init_command(self):
        """Initialize command."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        return ReportInsightsCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        # different from most other test cases where command is initialized once per
        # class, this one requires to be initialized for each test method because
        # SourceEditCommand instance modifies req_path on the fly. This seems to be a
        # code smell to me, but I'm choosing to ignore it for now
        self.command = self._init_command()

    def test_insights_report_as_json(self, caplog, fake_tarball):
        """Testing retrieving insights report as json."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {
            "id": 1,
            "report_id": 1,
            "sources": [{"source_type": "vcenter"}],
        }
        get_report_url = get_server_location() + REPORT_URI + "1/insights/"
        get_report_json_data = {
            "id": 1,
            "report_id": 1,
            "hosts": {"00968d16-78b7-4bda-ab7d-668f3c0ef1ee": {"key": "value"}},
        }
        test_dict = {fake_tarball: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200, json=get_scanjob_json_data)
            mocker.get(
                get_report_url,
                status_code=200,
                headers={"X-Server-Version": VERSION},
                content=buffer_content,
            )

            args = Namespace(scan_job_id="1", report_id=None, path=fake_tarball)
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.REPORT_SUCCESSFULLY_WRITTEN in caplog.text

    def test_insights_report_as_json_report_id(self, caplog, fake_tarball):
        """Testing retreiving insights report as json with report id."""
        scanjob_report_url = get_server_location() + SCAN_JOB_V2_URI + "?report_id=1"
        scanjob_data = {"results": [{"sources": [{"source_type": "network"}]}]}
        get_report_url = get_server_location() + REPORT_URI + "1/insights/"
        get_report_json_data = {
            "id": 1,
            "report_id": 1,
            "hosts": {"00968d16-78b7-4bda-ab7d-668f3c0ef1ee": {"key": "value"}},
        }
        test_dict = {fake_tarball: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(
                scanjob_report_url,
                status_code=200,
                headers={"X-Server-Version": VERSION},
                json=scanjob_data,
            )
            mocker.get(
                get_report_url,
                status_code=200,
                headers={"X-Server-Version": VERSION},
                content=buffer_content,
            )

            args = Namespace(scan_job_id=None, report_id="1", path=fake_tarball)
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert messages.REPORT_SUCCESSFULLY_WRITTEN in caplog.text

    # Test validation
    def test_insights_report_output_directory(self):
        """Testing fail because output directory."""
        with pytest.raises(SystemExit):
            sys.argv = ["/bin/qpc", "report", "insights", "--output-file", "/"]
            CLI().main()

    def test_insights_report_output_directory_not_exist(self):
        """Testing fail because output directory does not exist."""
        with pytest.raises(SystemExit):
            sys.argv = ["/bin/qpc", "report", "insights", "--output-file", "/foo/bar/"]
            CLI().main()

    def test_insights_report_output_file_empty(self):
        """Testing fail because output file empty."""
        with pytest.raises(SystemExit):
            sys.argv = ["/bin/qpc", "report", "insights", "--output-file", ""]
            CLI().main()

    def test_insights_report_scan_job_not_exist(self, fake_tarball):
        """Deployments report with nonexistent scanjob."""
        report_out = StringIO()

        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=400, json=get_scanjob_json_data)

            args = Namespace(scan_job_id="1", report_id=None, path=fake_tarball)
            with pytest.raises(SystemExit):
                with redirect_stdout(report_out):
                    self.command.main(args)
                    assert report_out.getvalue() == messages.REPORT_SJ_DOES_NOT_EXIST

    def test_insights_report_invalid_scan_job(self, fake_tarball):
        """Deployments report with scanjob but no report_id."""
        report_out = StringIO()

        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200, json=get_scanjob_json_data)

            args = Namespace(scan_job_id="1", report_id=None, path=fake_tarball)
            with pytest.raises(SystemExit):
                with redirect_stdout(report_out):
                    self.command.main(args)
                    assert (
                        report_out.getvalue()
                        == messages.REPORT_NO_DEPLOYMENTS_REPORT_FOR_SJ
                    )

    @patch("qpc.report.insights.write_file")
    def test_insights_file_fails_to_write(self, file, caplog, fake_tarball):
        """Testing insights failure while writing to file."""
        file.side_effect = EnvironmentError()
        scanjob_report_url = get_server_location() + SCAN_JOB_V2_URI + "?report_id=1"
        scanjob_data = {"results": [{"sources": [{"source_type": "network"}]}]}
        get_report_url = get_server_location() + REPORT_URI + "1/insights/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {fake_tarball: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(
                scanjob_report_url,
                status_code=200,
                headers={"X-Server-Version": VERSION},
                json=scanjob_data,
            )
            mocker.get(
                get_report_url,
                status_code=200,
                headers={"X-Server-Version": VERSION},
                content=buffer_content,
            )

            args = Namespace(scan_job_id=None, report_id="1", path=fake_tarball)
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.WRITE_FILE_ERROR % {
                    "path": fake_tarball,
                    "error": "",
                }
                assert err_msg in caplog.text

    def test_insights_nonexistent_directory(self, caplog, fake_tarball):
        """Testing error for nonexistent directory in output."""
        fake_dir = "/kevan/is/awesome/insights.tar.gz"
        get_report_url = get_server_location() + REPORT_URI + "1/insights/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {fake_tarball: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_report_url, status_code=200, content=buffer_content)

            args = Namespace(scan_job_id=None, report_id="1", path=fake_dir)
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = (
                    messages.REPORT_DIRECTORY_DOES_NOT_EXIST % Path(fake_dir).parent
                )
                assert err_msg in caplog.text

    def test_insights_tar_path(self, caplog, fake_tarball):
        """Testing error for nonjson output path."""
        non_tar_file = "/Users/insights.json"
        get_report_url = get_server_location() + REPORT_URI + "1/insights/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {fake_tarball: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(
                get_report_url,
                status_code=200,
                headers={"X-Server-Version": VERSION},
                content=buffer_content,
            )

            args = Namespace(scan_job_id=None, report_id="1", path=non_tar_file)
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.OUTPUT_FILE_TYPE % "tar.gz"
                assert err_msg in caplog.text

    def test_insights_report_id_not_exist(self, caplog, fake_tarball):
        """Test insights with nonexistent report id."""
        scanjob_report_url = get_server_location() + SCAN_JOB_V2_URI + "?report_id=1"
        get_report_url = get_server_location() + REPORT_URI + "1/insights/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {fake_tarball: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(
                scanjob_report_url,
                status_code=404,
                headers={"X-Server-Version": VERSION},
            )
            mocker.get(
                get_report_url,
                status_code=400,
                headers={"X-Server-Version": VERSION},
                content=buffer_content,
            )

            args = Namespace(scan_job_id=None, report_id="1", path=fake_tarball)
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_NO_INSIGHTS_REPORT_FOR_REPORT_ID % 1
                assert err_msg in caplog.text

    def test_insights_report_error_scan_job(self, caplog, fake_tarball):
        """Testing error with scan job id."""
        get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
        get_scanjob_json_data = {"id": 1, "report_id": 1}
        get_report_url = get_server_location() + REPORT_URI + "1/insights/"
        get_report_json_data = {"id": 1, "report": [{"key": "value"}]}
        test_dict = {fake_tarball: get_report_json_data}
        buffer_content = create_tar_buffer(test_dict)
        with requests_mock.Mocker() as mocker:
            mocker.get(get_scanjob_url, status_code=200, json=get_scanjob_json_data)
            mocker.get(
                get_report_url,
                status_code=400,
                headers={"X-Server-Version": VERSION},
                content=buffer_content,
            )

            args = Namespace(scan_job_id="1", report_id=None, path=fake_tarball)
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit):
                    self.command.main(args)
                err_msg = messages.REPORT_NO_INSIGHTS_REPORT_FOR_SJ % 1
                assert err_msg in caplog.text


def test_insights_report_as_json_no_output_file(caplog, capsys, requests_mock):
    """Testing retrieving insights report as json without output file."""
    caplog.set_level("INFO")
    scanjob_report_url = get_server_location() + SCAN_JOB_V2_URI + "?report_id=1"
    scanjob_data = {"results": [{"sources": [{"source_type": "network"}]}]}
    requests_mock.get(
        scanjob_report_url,
        status_code=200,
        json=scanjob_data,
        headers={"X-Server-Version": VERSION},
    )
    report_url = get_server_location() + REPORT_URI + "1/insights/"
    report_json_data = {
        "id": 1,
        "report_id": 1,
        "hosts": {"00968d16-78b7-4bda-ab7d-668f3c0ef1ee": {"key": "value"}},
    }
    json_filename = f"test_{time.time():.0f}.json"
    expected_json = {json_filename: report_json_data}
    requests_mock.get(
        report_url,
        status_code=200,
        json=expected_json,
        headers={"X-Server-Version": VERSION},
    )
    sys.argv = [
        "/bin/qpc",
        "report",
        "insights",
        "--report",
        "1",
    ]
    CLI().main()
    captured = capsys.readouterr()
    assert caplog.messages[-1] == messages.REPORT_SUCCESSFULLY_WRITTEN
    assert json.loads(captured.out)


def test_insights_not_available_scan_job(caplog, capsys, requests_mock):
    """Insights report can't be downloaded if only source is ansible.

    Insights report exist only if at least one of the sources is in
    {network, satellite, vcenter}. If all sources are using different
    type, report can't be downloaded. This test tries to download report
    using --scan-job param.
    """
    caplog.set_level("INFO")
    get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
    get_scanjob_json_data = {
        "id": 1,
        "report_id": 1,
        "sources": [{"source_type": "ansible"}],
    }
    requests_mock.get(get_scanjob_url, status_code=200, json=get_scanjob_json_data)
    sys.argv = [
        "/bin/qpc",
        "report",
        "insights",
        "--scan-job",
        "1",
    ]
    with caplog.at_level(logging.ERROR):
        with pytest.raises(SystemExit):
            CLI().main()
        err_msg = messages.REPORT_NO_INSIGHTS_REPORT_FOR_SJ % 1
        assert err_msg in caplog.text
        assert messages.REPORT_NO_INSIGHTS_CLARIFICATION in caplog.text


def test_insights_not_available_report_id(caplog, capsys, requests_mock):
    """Insights report can't be downloaded if only source is ansible.

    Insights report exist only if at least one of the sources is in
    {network, satellite, vcenter}. If all sources are using different
    type, report can't be downloaded. This test tries to download report
    using --report param.
    """
    caplog.set_level("INFO")
    scanjob_report_url = get_server_location() + SCAN_JOB_V2_URI + "?report_id=1"
    scanjob_data = {"results": [{"sources": [{"source_type": "ansible"}]}]}
    requests_mock.get(
        scanjob_report_url,
        status_code=200,
        json=scanjob_data,
        headers={"X-Server-Version": VERSION},
    )
    sys.argv = [
        "/bin/qpc",
        "report",
        "insights",
        "--report",
        "1",
    ]
    with caplog.at_level(logging.ERROR):
        with pytest.raises(SystemExit):
            CLI().main()
        err_msg = messages.REPORT_NO_INSIGHTS_REPORT_FOR_REPORT_ID % 1
        assert err_msg in caplog.text
        assert messages.REPORT_NO_INSIGHTS_CLARIFICATION in caplog.text


def test_insights_mix_sources_scan_job(caplog, capsys, requests_mock):
    """Insights report can be downloaded if one source is satellite.

    Insights report exist only if at least one of the sources is in
    {network, satellite, vcenter}. This test tries to download report
    using --scan-job param.
    """
    caplog.set_level("INFO")
    get_scanjob_url = get_server_location() + SCAN_JOB_URI + "1"
    get_scanjob_json_data = {
        "id": 1,
        "report_id": 1,
        "sources": [{"source_type": "ansible"}, {"source_type": "satellite"}],
    }
    requests_mock.get(get_scanjob_url, status_code=200, json=get_scanjob_json_data)
    report_url = get_server_location() + REPORT_URI + "1/insights/"
    report_json_data = {
        "id": 1,
        "report_id": 1,
        "hosts": {"00968d16-78b7-4bda-ab7d-668f3c0ef1ee": {"key": "value"}},
    }
    json_filename = f"test_{time.time():.0f}.json"
    expected_json = {json_filename: report_json_data}
    requests_mock.get(
        report_url,
        status_code=200,
        json=expected_json,
        headers={"X-Server-Version": VERSION},
    )
    sys.argv = [
        "/bin/qpc",
        "report",
        "insights",
        "--scan-job",
        "1",
    ]
    CLI().main()
    captured = capsys.readouterr()
    assert caplog.messages[-1] == messages.REPORT_SUCCESSFULLY_WRITTEN
    assert json.loads(captured.out)


def test_insights_mix_sources_report_id(caplog, capsys, requests_mock):
    """Insights report can be downloaded if one source is network.

    Insights report exist only if at least one of the sources is in
    {network, satellite, vcenter}. This test tries to download report
    using --report param.
    """
    caplog.set_level("INFO")
    scanjob_report_url = get_server_location() + SCAN_JOB_V2_URI + "?report_id=1"
    scanjob_data = {
        "results": [
            {"sources": [{"source_type": "ansible"}, {"source_type": "satellite"}]}
        ]
    }
    requests_mock.get(
        scanjob_report_url,
        status_code=200,
        json=scanjob_data,
        headers={"X-Server-Version": VERSION},
    )
    report_url = get_server_location() + REPORT_URI + "1/insights/"
    report_json_data = {
        "id": 1,
        "report_id": 1,
        "hosts": {"00968d16-78b7-4bda-ab7d-668f3c0ef1ee": {"key": "value"}},
    }
    json_filename = f"test_{time.time():.0f}.json"
    expected_json = {json_filename: report_json_data}
    requests_mock.get(
        report_url,
        status_code=200,
        json=expected_json,
        headers={"X-Server-Version": VERSION},
    )
    sys.argv = [
        "/bin/qpc",
        "report",
        "insights",
        "--report",
        "1",
    ]
    CLI().main()
    captured = capsys.readouterr()
    assert caplog.messages[-1] == messages.REPORT_SUCCESSFULLY_WRITTEN
    assert json.loads(captured.out)
