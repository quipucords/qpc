"""Test openshift source edit in CLI."""

import sys

import pytest

from qpc import messages
from qpc.cli import CLI
from qpc.source import SOURCE_URI
from qpc.utils import get_server_location


@pytest.fixture
def ocp_source_mock(requests_mock, ocp_credential_mock):
    """Return ocp source."""
    get_source_url = get_server_location() + SOURCE_URI + "?name=ocp_source_1"
    source_results = [
        {
            "id": 1,
            "name": "ocp_source_1",
            "hosts": ["1.2.3.4"],
            "credentials": [{"id": 1, "name": "ocp_cred_1"}],
        }
    ]
    ocp_source_data = {"count": 1, "results": source_results}
    yield requests_mock.get(get_source_url, status_code=200, json=ocp_source_data)


class TestOpenShiftEditSource:
    """Class for testing OpenShift edit source."""

    def test_edit_partial_green_path(
        self,
        caplog,
        requests_mock,
        ocp_source_mock,
    ):
        """Test partial openshift edit source successfully."""
        caplog.set_level("INFO")
        url_patch = get_server_location() + SOURCE_URI + "1/"
        requests_mock.patch(url_patch, status_code=200)
        sys.argv = [
            "/bin/qpc",
            "source",
            "edit",
            "--name",
            "ocp_source_1",
            "--host",
            "[4.3.2.1]",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.SOURCE_UPDATED % "ocp_source_1"

    def test_full_edit(
        self,
        caplog,
        requests_mock,
        ocp_source_mock,
    ):
        """Test full openshift edit source successfully."""
        caplog.set_level("INFO")
        url_patch = get_server_location() + SOURCE_URI + "1/"
        requests_mock.patch(url_patch, status_code=200)
        sys.argv = [
            "/bin/qpc",
            "source",
            "edit",
            "--name",
            "ocp_source_1",
            "--host",
            "[4.3.2.1]",
            "--port",
            "200",
            "--ssl-protocol",
            "TLSv1_2",
            "--ssl-cert-verify",
            "true",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.SOURCE_UPDATED % "ocp_source_1"

    @pytest.mark.parametrize(
        "status_code,err_log_message",
        [
            (401, "qpc server login"),
            (500, "An internal server error occurred."),
        ],
    )
    def test_edit_returning_error(
        self,
        capsys,
        requests_mock,
        status_code,
        err_log_message,
    ):
        """Test openshift edit source w/ errors."""
        url_get = get_server_location() + SOURCE_URI
        requests_mock.get(url_get, status_code=status_code, json=None)
        sys.argv = [
            "/bin/qpc",
            "source",
            "edit",
            "--name",
            "ocp_source_2",
            "--disable-ssl",
            "true",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert err_log_message in err

    def test_edit_incorrect_arg(self, capsys, requests_mock):
        """Test ocp edit w/ incorrect arg."""
        url_patch = get_server_location() + SOURCE_URI + "1/"
        requests_mock.patch(url_patch, status_code=400)
        sys.argv = [
            "/bin/qpc",
            "source",
            "edit",
            "--name",
            "ocp_source_1",
            "--host",
            "[4.3.2.1]",
            "--disable-sssl",
            "true",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        expected_output = "error: unrecognized arguments: --disable-sssl true\n"
        out, err = capsys.readouterr()
        assert out == ""
        assert expected_output in err
