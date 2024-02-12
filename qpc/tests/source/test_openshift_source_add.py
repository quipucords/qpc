"""Test openshift source add in CLI."""

import sys

import pytest

from qpc import messages
from qpc.cli import CLI
from qpc.source import OPENSHIFT_SOURCE_TYPE, SOURCE_URI
from qpc.utils import get_server_location


class TestOpenShiftAddSource:
    """Class for testing OCP add source."""

    @pytest.mark.parametrize("ocp_source_type", ["openshift", "OPENSHIFT", "OpenShift"])
    def test_add_green_path(
        self, caplog, ocp_credential_mock, requests_mock, ocp_source_type
    ):
        """Test ocp source add green path."""
        caplog.set_level("INFO")
        url = get_server_location() + SOURCE_URI
        requests_mock.post(url, status_code=201)
        sys.argv = [
            "/bin/qpc",
            "source",
            "add",
            "--name",
            "ocp_source_1",
            "--type",
            ocp_source_type,
            "--cred",
            "ocp_cred_1",
            "--hosts",
            "[1.2.3.4]",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.SOURCE_ADDED % "ocp_source_1"

    @pytest.mark.parametrize(
        "ssl_cert_verify_values", ["false", "False", "FALSE", "FaLsE"]
    )
    def test_add_no_ssl_cert(
        self, caplog, ocp_credential_mock, requests_mock, ssl_cert_verify_values
    ):
        """Test ocp add source w/ ssl_cert_verify=false."""
        caplog.set_level("INFO")
        url = get_server_location() + SOURCE_URI
        requests_mock.post(url, status_code=201)
        sys.argv = [
            "/bin/qpc",
            "source",
            "add",
            "--name",
            "ocp_source_1",
            "--type",
            OPENSHIFT_SOURCE_TYPE,
            "--cred",
            "ocp_cred_1",
            "--hosts",
            "[1.2.3.4]",
            "--ssl-cert-verify",
            ssl_cert_verify_values,
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.SOURCE_ADDED % "ocp_source_1"

    @pytest.mark.parametrize("disable_ssl_values", ["false", "False", "FALSE", "FaLsE"])
    def test_add_with_ssl_params(
        self, caplog, ocp_credential_mock, requests_mock, disable_ssl_values
    ):
        """Test ocp add source w/ ssl_cert_verify=false."""
        caplog.set_level("INFO")
        url = get_server_location() + SOURCE_URI
        requests_mock.post(url, status_code=201)
        sys.argv = [
            "/bin/qpc",
            "source",
            "add",
            "--name",
            "ocp_source_1",
            "--type",
            OPENSHIFT_SOURCE_TYPE,
            "--cred",
            "ocp_cred_1",
            "--hosts",
            "[1.2.3.4]",
            "--ssl-cert-verify",
            "true",
            "--disable-ssl",
            disable_ssl_values,
            "--ssl-protocol",
            "TLSv1_2",
            "--port",
            "200",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.SOURCE_ADDED % "ocp_source_1"

    def test_add_with_unknown_ssl_param(self, capsys, ocp_credential_mock):
        """Test ocp add source w/ unknown ssl param."""
        sys.argv = [
            "/bin/qpc",
            "source",
            "add",
            "--name",
            "ocp_source_1",
            "--type",
            OPENSHIFT_SOURCE_TYPE,
            "--cred",
            "ocp_cred_1",
            "--hosts",
            "[1.2.3.4]",
            "--ssl-cert-verify",
            "true",
            "--disable-ssl",
            "false",
            "--ssl-protocol",
            "unknown_ssl_protocol",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        expected_output = "--ssl-protocol: invalid choice: 'unknown_ssl_protocol'"
        out, err = capsys.readouterr()
        assert out == ""
        assert expected_output in err

    @pytest.mark.parametrize(
        "status_code, err_log_message",
        [
            (401, "qpc server login"),
            (500, "An internal server error occurred."),
        ],
    )
    def test_add_returning_error(
        self, capsys, requests_mock, ocp_credential_mock, status_code, err_log_message
    ):
        """Test ocp source add with errors."""
        url = get_server_location() + SOURCE_URI
        requests_mock.post(url, status_code=status_code)
        sys.argv = [
            "/bin/qpc",
            "source",
            "add",
            "--name",
            "ocp_source_1",
            "--type",
            OPENSHIFT_SOURCE_TYPE,
            "--cred",
            "ocp_cred_1",
            "--hosts",
            "[1.2.3.4]",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert err_log_message in err
        assert out == ""
