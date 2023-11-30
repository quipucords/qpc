"""pytest configuration file."""

import pytest

from qpc.cred import CREDENTIAL_URI


@pytest.fixture(autouse=True)
def _setup_server_config_file(server_config):
    ...


@pytest.fixture
def ocp_credential_mock(requests_mock):
    """Return ocp credential."""
    from qpc.utils import get_server_location

    get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=ocp_cred_1"
    cred_results = [{"id": 1, "name": "ocp_cred_1"}]
    ocp_cred_data = {"count": 1, "results": cred_results}
    yield requests_mock.get(get_cred_url, status_code=200, json=ocp_cred_data)
