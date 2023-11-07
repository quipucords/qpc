# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""pytest configuration file."""

from unittest import mock

import pytest

QPC_PATH_CONSTANTS = (
    "CONFIG_DIR",
    "DATA_DIR",
    "INSIGHTS_CONFIG",
    "INSIGHTS_ENCRYPTION",
    "INSIGHTS_AUTH_TOKEN",
    "QPC_CLIENT_TOKEN",
    "QPC_LOG",
    "QPC_SERVER_CONFIG",
)


@pytest.fixture(autouse=True)
def mock_path_constants(tmp_path, monkeypatch):
    """Mock path constants used on qpc."""
    for path in QPC_PATH_CONSTANTS:
        monkeypatch.setattr(f"qpc.utils.{path}", tmp_path / path)


def _set_path_constants_to_none():
    """Set qpc path constants to None."""
    for constant in QPC_PATH_CONSTANTS:
        mocker = mock.patch(f"qpc.utils.{constant}", None)
        mocker.start()


def pytest_collection(session):
    """pytest collection hook.

    This function runs before collecting tests.
    """
    # setting path constants to None on utils module is a dirty way to ensure
    # no test will write on top of user config file. This is a last resort, as
    # mock_path_constants fixture shall be doing the job of actually patching
    # those to a usable value in tests
    _set_path_constants_to_none()


@pytest.fixture
def server_config():
    """
    Create server config with require_token set to False.

    Since all cli commands require qpc config and qpc login to be executed,
    require_token must be False, to avoid passing login info
    """
    from qpc.utils import write_server_config

    return write_server_config(
        {
            "host": "127.0.0.1",
            "port": 8000,
            "use_http": True,
            "require_token": False,
        }
    )
