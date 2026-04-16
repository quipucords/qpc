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


@pytest.fixture
def client_cert(tmp_path, test_cert_content):
    """Create a test client certificate file."""
    client_cert = tmp_path / "client.pem"
    client_cert.write_bytes(test_cert_content)
    return client_cert


@pytest.fixture
def client_key(tmp_path, test_key_content):
    """Create a test client key file."""
    client_key = tmp_path / "client-key.pem"
    client_key.write_bytes(test_key_content)
    return client_key


@pytest.fixture
def ca_cert(tmp_path, test_cert_content):
    """Create a test CA cert file."""
    ca_cert = tmp_path / "ca.pem"
    ca_cert.write_bytes(test_cert_content)
    return ca_cert
