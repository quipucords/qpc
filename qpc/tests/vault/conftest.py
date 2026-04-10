"""pytest configuration file for vault tests."""

import pytest


@pytest.fixture(autouse=True)
def _setup_server_config_file(authenticated_client): ...
