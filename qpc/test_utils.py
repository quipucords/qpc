"""Test qpc cred utils."""
import pytest

from qpc.messages import PROMPT_INPUT
from qpc.utils import check_if_prompt_is_not_empty


@pytest.mark.parametrize("pass_prompt", ["", None])
def test_invalid_pass_prompt(pass_prompt, caplog):
    """Test if error will be raised when prompt is empty."""
    caplog.set_level("ERROR")
    with pytest.raises(SystemExit):
        check_if_prompt_is_not_empty(pass_prompt)
    assert caplog.messages[-1] == PROMPT_INPUT
