"""pytest configuration file."""

import pytest


@pytest.fixture(autouse=True)
def _setup_server_config_file(authenticated_client): ...


@pytest.fixture
def openshift_token_input(monkeypatch):
    """Mock Openshift token return from prompt."""
    yield monkeypatch.setattr(
        "qpc.cred.utils.getpass", lambda x: "mocked_input_password"
    )
