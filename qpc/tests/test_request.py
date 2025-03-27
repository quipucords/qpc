"""QPC request tests."""

from unittest.mock import MagicMock, patch

import pytest

from qpc.request import request, version_tuple
from qpc.utils import CLIENT_TOKEN_TEST_VALUE, QPC_MIN_SERVER_VERSION


def test_request_invalid_method(server_config, caplog):
    """Test request with an invalid http method."""
    caplog.set_level("ERROR")
    parser_mock = MagicMock()
    with pytest.raises(SystemExit):
        with patch("builtins.print"):
            with patch("argparse.ArgumentParser.print_help"):
                request("INVALID_METHOD", "/path", parser=parser_mock)
    assert caplog.messages[-1] == "Unsupported request method INVALID_METHOD"


@pytest.mark.parametrize("method", ["GET", "DELETE", "PUT", "POST", "PATCH"])
def test_request_methods(authenticated_client, method):
    """Test request with valid http methods."""
    with patch("qpc.request.perform_request") as mock_perform_request:
        request(method, "/path")
        mock_perform_request.assert_called_once_with(
            method,
            "http://127.0.0.1:8000/path",
            None,
            None,
            {"Authorization": f"Token {CLIENT_TOKEN_TEST_VALUE}"},
            QPC_MIN_SERVER_VERSION,
        )


def test_log_request_info_invalid_json(server_config, caplog):
    """Test log_request_info with invalid json."""
    caplog.set_level("DEBUG")
    response = MagicMock()
    response.status_code = 200
    response.json.side_effect = ValueError("Invalid JSON")

    with patch("qpc.request.perform_request", return_value=response):
        request("GET", "/path")

    assert 'Response: "<encoded blob ignored>"' in caplog.messages[-1]


def test_log_request_info_valid_json(server_config, caplog):
    """Test log_request_info with valid json."""
    caplog.set_level("DEBUG")
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"message": "Success"}

    with patch("qpc.request.perform_request", return_value=response):
        request("GET", "/path")

    assert "Response: \"{'message': 'Success'}\"" in caplog.messages[-1]


@pytest.mark.parametrize(
    "version_string,expected_result",
    [
        ["1.2.3", (1, 2, 3)],
        ["1.2.3.4", (1, 2, 3)],
        ["010.20.3", (10, 20, 3)],
        ["1.2.3+c0ff33", (1, 2, 3)],
        ["1.2.3a1", (1, 2, 3)],
        ["1.2.3.dev4", (1, 2, 3)],
    ],
)
def test_version_tuple(version_string, expected_result):
    """Test converting version strings to tuples."""
    assert version_tuple(version_string) == expected_result


@pytest.mark.parametrize(
    "version_string",
    ["1.2", "1.2.dev3", "1!2.3", "1.2a3.4", "1.2.post-3", "a.b.c"],
)
def test_version_tuple_invalid(version_string):
    """Test failing to convert unsupported version strings to tuples."""
    with pytest.raises(ValueError):
        version_tuple(version_string)
