"""pytest configuration file for vault tests."""

import pytest


@pytest.fixture(autouse=True)
def _setup_server_config_file(authenticated_client): ...


@pytest.fixture
def test_cert_content():
    """Return the content of a test Certificate."""
    return b"-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"


@pytest.fixture
def test_key_content():
    """Return the content of a test Key."""
    return b"-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"
