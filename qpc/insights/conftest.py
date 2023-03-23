"""pytest configuration file."""

import pytest


@pytest.fixture(autouse=True)
def _setup_server_config_file(server_config):
    """Disable the server_config feature in conftest's root folder."""
    # We wanted the fixture to be widely available,
    # but only called when necessary as we use autouse flag


@pytest.fixture
def insights_login_password_input(monkeypatch):
    """Mock insights add_login return password from prompt."""
    yield monkeypatch.setattr(
        "qpc.insights.utils.getpass", lambda x: "insights-test-password"
    )
