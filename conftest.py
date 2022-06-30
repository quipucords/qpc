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

import pytest

QPC_PATH_CONSTANTS = (
    "CONFIG_DIR",
    "DATA_DIR",
    "QPC_CLIENT_TOKEN",
    "QPC_LOG",
    "QPC_SERVER_CONFIG",
)


@pytest.fixture(autouse=True)
def mock_path_constants(tmp_path, monkeypatch):
    """Mock path constants used on qpc."""
    for path in QPC_PATH_CONSTANTS:
        monkeypatch.setattr(f"qpc.utils.{path}", str(tmp_path / path))

