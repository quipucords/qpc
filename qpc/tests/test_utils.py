"""Test qpc cred utils."""

import pytest

from qpc.messages import PROMPT_INPUT
from qpc.utils import check_if_prompt_is_not_empty, json_data_deep_get


@pytest.mark.parametrize("pass_prompt", ["", None])
def test_invalid_pass_prompt(pass_prompt, caplog):
    """Test if error will be raised when prompt is empty."""
    caplog.set_level("ERROR")
    with pytest.raises(SystemExit):
        check_if_prompt_is_not_empty(pass_prompt)
    assert caplog.messages[-1] == PROMPT_INPUT


@pytest.mark.parametrize(
    "json_data, key_path, expected_result",
    [
        ({"k1": "v1", "k2": "v2"}, "", None),
        ({"k1": "v1", "k2": "v2"}, "k2", "v2"),
        ({"k1": "v1", "k2": "v2"}, "missing", None),
        ({"l1": {"l2": {"l3": "v3"}}}, "l1.l2.l3", "v3"),
        ({"l1": {"l2": {"l3": "v3"}}}, "l1.missing.l3", None),
    ],
)
def test_json_data_deep_get(json_data, key_path, expected_result):
    """Test json_data_deep_get function."""
    result = json_data_deep_get(json_data, key_path)
    assert result == expected_result
