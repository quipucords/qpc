# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test qpc path constants."""

import pytest

from qpc.utils import (
    CONFIG_DIR,
    DATA_DIR,
    INSIGHTS_CONFIG,
    INSIGHTS_LOGIN_CONFIG,
    QPC_CLIENT_TOKEN,
    QPC_LOG,
    QPC_SERVER_CONFIG,
)


@pytest.mark.parametrize(
    "path_constant",
    (
        CONFIG_DIR,
        DATA_DIR,
        INSIGHTS_CONFIG,
        INSIGHTS_LOGIN_CONFIG,
        QPC_CLIENT_TOKEN,
        QPC_LOG,
        QPC_SERVER_CONFIG,
    ),
)
def test_path_constant_is_patched(path_constant):
    """
    Ensure path constants are set to None if imported directly.

    Mocking global variables is a tricky thing if they are imported as in this module
    and is discouraged to simplify this process.
    """
    assert path_constant is None
