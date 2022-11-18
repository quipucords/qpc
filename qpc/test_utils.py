# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
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
