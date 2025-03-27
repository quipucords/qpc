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
    Create server config.

    Tests that want to pass the initial login check, should also use client_token
    fixture, or use only authenticated_client fixture (which pulls both server_config
    and client_token).
    """
    from qpc.utils import (
        CONFIG_HOST_KEY,
        CONFIG_PORT_KEY,
        CONFIG_USE_HTTP,
        write_server_config,
    )

    return write_server_config(
        {
            CONFIG_HOST_KEY: "127.0.0.1",
            CONFIG_PORT_KEY: 8000,
            CONFIG_USE_HTTP: True,
        }
    )


@pytest.fixture
def client_token():
    """Create fake client token."""
    from qpc.utils import CLIENT_TOKEN_KEY, CLIENT_TOKEN_TEST_VALUE, write_client_token

    write_client_token({CLIENT_TOKEN_KEY: CLIENT_TOKEN_TEST_VALUE})


@pytest.fixture
def authenticated_client(server_config, client_token):
    """Create server config and client token, providing authenticated client setup.

    Tests that wish to use unauthenticated client, should use server_config fixture.
    """
    pass
