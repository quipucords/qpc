"""Test the "report aggregate" subcommand."""

import logging
from argparse import ArgumentParser, Namespace
from unittest.mock import patch

import pytest
import requests_mock

from qpc import messages
from qpc.report import AGGREGATE_PATH_SUFFIX, REPORT_URI
from qpc.report.aggregate import ReportAggregateCommand
from qpc.scan import SCAN_JOB_URI
from qpc.utils import get_server_location


def get_scan_job_uri(scan_job_id: int) -> str:
    """Construct a scan job URI for testing."""
    return f"{get_server_location()}{SCAN_JOB_URI}{scan_job_id}"


def get_aggregate_report_uri(report_id: int) -> str:
    """Construct an aggregate report URI for testing."""
    return f"{get_server_location()}{REPORT_URI}{report_id}{AGGREGATE_PATH_SUFFIX}"


def get_command():
    """Set up new command for each test."""
    # We can't use a fixture for this, even though that seems reasonable,
    # because our command instances modify req_path on the fly. This is
    # definitely a bad code smell, but we are choosing to ignore it because
    # this design issue affects many of our commands and tests the same way.
    argument_parser = ArgumentParser()
    subparser = argument_parser.add_subparsers(dest="subcommand")
    return ReportAggregateCommand(subparser)


@patch("qpc.report.aggregate.pretty_format")
def test_aggregate_report_success_via_report(mock_pretty_format, faker, capsys):
    """Test aggregate report with report id."""
    report_id = faker.pyint()
    report_uri = get_aggregate_report_uri(report_id)
    report_json_data = {faker.slug(): faker.slug()}
    with requests_mock.Mocker() as mocker:
        mocker.get(report_uri, status_code=200, json=report_json_data)
        args = Namespace(scan_job_id=None, report_id=report_id)
        get_command().main(args)
    mock_pretty_format.assert_called_once_with(report_json_data)
    out, err = capsys.readouterr()
    assert str(mock_pretty_format.return_value) in out
    assert not err


@patch("qpc.report.aggregate.pretty_format")
def test_aggregate_report_success_via_scan_job(mock_pretty_format, faker, capsys):
    """Test aggregate report with scan job id."""
    report_id = faker.pyint()
    scan_job_id = faker.pyint()
    scan_job_uri = get_scan_job_uri(scan_job_id)
    scan_job_json_data = {"id": scan_job_id, "report_id": report_id}
    aggregate_report_uri = get_aggregate_report_uri(report_id)
    aggregate_report_json_data = {faker.slug(): faker.slug()}
    with requests_mock.Mocker() as mocker:
        mocker.get(scan_job_uri, status_code=200, json=scan_job_json_data)
        mocker.get(
            aggregate_report_uri, status_code=200, json=aggregate_report_json_data
        )
        args = Namespace(scan_job_id=scan_job_id, report_id=None)
        get_command().main(args)
    mock_pretty_format.assert_called_once_with(aggregate_report_json_data)
    out, err = capsys.readouterr()
    assert str(mock_pretty_format.return_value) in out
    assert not err


def test_aggregate_report_but_scan_job_does_not_exist(faker, caplog):
    """Test aggregate report with scan job id that does not exist."""
    scan_job_id = faker.pyint()
    scan_job_uri = get_scan_job_uri(scan_job_id)
    with requests_mock.Mocker() as mocker:
        mocker.get(scan_job_uri, status_code=400)
        args = Namespace(scan_job_id=scan_job_id, report_id=None)
        with pytest.raises(SystemExit):
            get_command().main(args)

    expected_error = messages.REPORT_SJ_DOES_NOT_EXIST % scan_job_id
    assert expected_error in caplog.text


def test_deployments_report_but_scan_job_has_no_report(faker, caplog):
    """Test aggregate report with scan job id that has no report id."""
    scan_job_id = faker.pyint()
    scan_job_uri = get_scan_job_uri(scan_job_id)
    scan_job_json_data = {"id": scan_job_id}
    with requests_mock.Mocker() as mocker:
        mocker.get(scan_job_uri, status_code=200, json=scan_job_json_data)
        args = Namespace(scan_job_id=scan_job_id, report_id=None)
        with pytest.raises(SystemExit):
            get_command().main(args)
    expected_error = messages.REPORT_NO_AGGREGATE_REPORT_FOR_SJ % scan_job_id
    assert expected_error in caplog.text


def test_aggregate_report_but_report_does_not_exist(faker, caplog):
    """Test aggregate report with nonexistent report id."""
    unknown_report_id = faker.pyint()
    aggregate_report_uri = get_aggregate_report_uri(unknown_report_id)
    with requests_mock.Mocker() as mocker:
        mocker.get(aggregate_report_uri, status_code=400)
        args = Namespace(scan_job_id=None, report_id=unknown_report_id)
        with caplog.at_level(logging.ERROR):
            with pytest.raises(SystemExit):
                get_command().main(args)
    expected_error = (
        messages.REPORT_NO_AGGREGATE_REPORT_FOR_REPORT_ID % unknown_report_id
    )
    assert expected_error in caplog.text
