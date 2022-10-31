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


@pytest.fixture(autouse=True)
def _setup_server_config_file(server_config):
    """Disable the server_config feature in conftest's root folder."""
    # We wanted the fixture to be widely available,
    # but only called when necessary as we use autouse flag

