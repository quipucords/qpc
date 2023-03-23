"""Test qpc path constants."""

import pytest

from qpc.utils import (
    CONFIG_DIR,
    DATA_DIR,
    INSIGHTS_CONFIG,
    INSIGHTS_ENCRYPTION,
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
        INSIGHTS_ENCRYPTION,
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
