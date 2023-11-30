"""QPC request tests."""

from unittest.mock import MagicMock, patch

import pytest

from qpc.request import request
from qpc.utils import QPC_MIN_SERVER_VERSION


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
def test_request_methods(server_config, method):
    """Test request with valid http methods."""
    with patch("qpc.request.perform_request") as mock_perform_request:
        request(method, "/path")
        mock_perform_request.assert_called_once_with(
            method,
            "http://127.0.0.1:8000/path",
            None,
            None,
            {},
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
