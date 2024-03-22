"""Test the "source add" command."""

import logging
import sys
from argparse import ArgumentParser, ArgumentTypeError, Namespace

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.cli import CLI
from qpc.cred import CREDENTIAL_URI
from qpc.request import CONNECTION_ERROR_MSG
from qpc.source import SOURCE_URI
from qpc.source.add import SourceAddCommand
from qpc.source.utils import validate_port
from qpc.tests.utilities import DEFAULT_CONFIG
from qpc.utils import get_server_location


@pytest.fixture
def hostsfile(tmp_path):
    """Return the path to a hostsfile for testing."""
    _file = tmp_path / "hostsfile"
    _file.write_text("1.2.3.4\n1.2.3.[1:10]\n")
    return str(_file)


@pytest.mark.usefixtures("server_config")
class TestSourceAddCli:
    """Class for testing the source add commands for qpc."""

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = SourceAddCommand(subparser)

    def test_add_req_args_err(self):
        """Testing the add source command required flags."""
        with pytest.raises(SystemExit):
            sys.argv = ["/bin/qpc", "source", "add", "--name", "source1"]
            CLI().main()

    def test_add_process_file(self, hostsfile, requests_mock, mocker):
        """Testing the add source command process file."""
        requests_mock.get(
            get_server_location() + CREDENTIAL_URI + "?name=cred1",
            status_code=200,
            json={"count": 1, "results": [{"id": 1, "name": "cred1"}]},
        )
        requests_mock.post(get_server_location() + SOURCE_URI, status_code=201)
        mocker.patch.object(
            sys,
            "argv",
            [
                "/bin/qpc",
                "source",
                "add",
                "--name",
                "source1",
                "--type",
                "network",
                "--hosts",
                hostsfile,
                "--cred",
                "cred1",
            ],
        )
        CLI().main()
        assert requests_mock.last_request.json() == {
            "name": "source1",
            "source_type": "network",
            "hosts": ["1.2.3.4", "1.2.3.[1:10]"],
            "credentials": [1],
            "port": None,
        }

    def test_validate_port_string(self):
        """Testing the add source command with port validation non-integer."""
        with pytest.raises(ArgumentTypeError) as e:
            validate_port("ff")
        assert "Port value ff" in str(e)

    def test_validate_port_bad_type(self):
        """Testing the add source command with port validation bad type."""
        with pytest.raises(ArgumentTypeError) as e:
            validate_port(["ff"])
        assert "Port value ['ff']" in str(e)

    def test_validate_port_range_err(self):
        """Test the add source command with port validation out of range."""
        msg = (
            "Port value {port} should be a positive integer"
            " in the valid range (0-65535)"
        )
        with pytest.raises(ArgumentTypeError) as e:
            validate_port("65537")
        assert msg.format(port="65537") in str(e)

    def test_validate_port_good(self):
        """Testing the add source command with port validation success."""
        val = validate_port("80")
        assert val == 80

    def test_add_source_name_dup(self, caplog):
        """Testing the add source command duplicate name."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        cred_results = [{"id": 1, "name": "cred1"}]
        get_cred_data = {"count": 1, "results": cred_results}
        post_source_url = get_server_location() + SOURCE_URI
        error = {"name": ["source with this name already exists."]}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=200, json=get_cred_data)
            mocker.post(post_source_url, status_code=400, json=error)

            args = Namespace(
                name="source_dup",
                cred=["cred1"],
                type="network",
                hosts=["1.2.3.4"],
                port=22,
            )
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert "source with this name already exists." in caplog.text

    def test_add_source_cred_less(self, caplog):
        """Testing the add source command with a some invalid cred."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1%2Ccred2"
        cred_results = [{"id": 1, "name": "cred1"}]
        get_cred_data = {"count": 1, "results": cred_results}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=200, json=get_cred_data)

            args = Namespace(
                name="source1",
                cred=["cred1", "cred2"],
                hosts=["1.2.3.4"],
                type="network",
                port=22,
            )
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert (
                'An error occurred while processing the "--cred" input' in caplog.text
            )

    @pytest.mark.skip(
        reason=(
            "FIXME! This test seems reasonable, but SourceAddCommand._validate_args "
            "logic incorrectly handles server error responses. Underlying code needs "
            "a thorough evaluation and rewrite."
        )
    )
    def test_add_source_cred_err(self, caplog):
        """Testing the add source command with a cred err."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1%2Ccred2"
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=500)

            args = Namespace(
                name="source1",
                cred=["cred1", "cred2"],
                hosts=["1.2.3.4"],
                type="network",
                port=22,
            )
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert (
                'An error occurred while processing the "--cred" input' in caplog.text
            )

    def test_add_source_ssl_err(self, caplog):
        """Testing the add source command with a connection error."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, exc=requests.exceptions.SSLError)

            args = Namespace(
                name="source1",
                cred=["cred1"],
                hosts=["1.2.3.4"],
                type="network",
                port=22,
            )
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected_error in caplog.text

    def test_add_source_conn_err(self, caplog):
        """Testing the add source command with a connection error."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        expected_error = CONNECTION_ERROR_MSG % {
            "host": DEFAULT_CONFIG["host"],
            "port": DEFAULT_CONFIG["port"],
            "protocol": "http",
        }
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, exc=requests.exceptions.ConnectTimeout)

            args = Namespace(
                name="source1",
                cred=["cred1"],
                hosts=["1.2.3.4"],
                type="network",
                port=22,
            )
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected_error in caplog.text

    ##################################################
    # Network Source Test
    ##################################################
    def test_add_source_net_one_host(self, caplog):
        """Testing add network source command successfully with one host."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        cred_results = [{"id": 1, "name": "cred1"}]
        get_cred_data = {"count": 1, "results": cred_results}
        post_source_url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=200, json=get_cred_data)
            mocker.post(post_source_url, status_code=201)

            args = Namespace(
                name="source1",
                cred=["cred1"],
                hosts=["1.2.3.4"],
                type="network",
                port=22,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_ADDED % "source1"
                assert expected_message in caplog.text

    def test_add_source_net_valid_hosts(self, caplog):
        """Testing add network source command with hosts in valid formats."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        cred_results = [{"id": 1, "name": "cred1"}]
        get_cred_data = {"count": 1, "results": cred_results}
        post_source_url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=200, json=get_cred_data)
            mocker.post(post_source_url, status_code=201)

            args = Namespace(
                name="source1",
                cred=["cred1"],
                hosts=[
                    "10.10.181.9",
                    "10.10.181.8/16",
                    "10.10.128.[1:25]",
                    "10.10.[1:20].25",
                    "localhost",
                    "mycentos.com",
                    "my-rhel[a:d].company.com",
                    "my-rhel[120:400].company.com",
                ],
                type="network",
                port=22,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_ADDED % "source1"
                assert expected_message in caplog.text

    def test_add_source_with_paramiko(self, caplog):
        """Testing add network source command with use_paramiko set to true."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        cred_results = [{"id": 1, "name": "cred1"}]
        get_cred_data = {"count": 1, "results": cred_results}
        post_source_url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=200, json=get_cred_data)
            mocker.post(post_source_url, status_code=201)

            args = Namespace(
                name="source1",
                cred=["cred1"],
                hosts=["10.10.181.9"],
                use_paramiko=True,
                type="network",
                port=22,
            )

            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_ADDED % "source1"
                assert expected_message in caplog.text

    def test_add_source_with_paramiko_and_ssl(self, caplog):
        """Testing add network source command with use_paramiko set to true."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        cred_results = [{"id": 1, "name": "cred1"}]
        get_cred_data = {"count": 1, "results": cred_results}
        post_source_url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=200, json=get_cred_data)
            mocker.post(post_source_url, status_code=400)

            args = Namespace(
                name="source1",
                cred=["cred1"],
                hosts=["10.10.181.9"],
                ssl_cert_verify="False",
                use_paramiko=True,
                type="network",
                port=22,
            )
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            # TODO Assert *something* meaningful is in the output!
            # assert caplog.text
            # FIXME utils.handle_error_response does literally nothing if the
            #  server's response is not JSON (raises JSONDecodeError).
            #  This means the process simply exits with NO OUTPUT.
            # TODO Underlying code needs a thorough evaluation and rewrite.

    def test_add_source_one_excludehost(self, caplog):
        """Testing the add network source command with one exclude host."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        cred_results = [{"id": 1, "name": "cred1"}]
        get_cred_data = {"count": 1, "results": cred_results}
        post_source_url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=200, json=get_cred_data)
            mocker.post(post_source_url, status_code=201)

            args = Namespace(
                name="source1",
                cred=["cred1"],
                hosts=["1.2.3.4"],
                type="network",
                exclude_hosts=["1.2.3.4"],
                port=22,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_ADDED % "source1"
                assert expected_message in caplog.text

    def test_add_source_exclude_hosts(self, caplog):
        """Testing add network source command with many valid exclude hosts."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        cred_results = [{"id": 1, "name": "cred1"}]
        get_cred_data = {"count": 1, "results": cred_results}
        post_source_url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=200, json=get_cred_data)
            mocker.post(post_source_url, status_code=201)

            args = Namespace(
                name="source1",
                cred=["cred1"],
                hosts=[
                    "10.10.181.9",
                    "10.10.181.8/16",
                    "10.10.128.[1:25]",
                    "10.10.[1:20].25",
                    "localhost",
                    "mycentos.com",
                    "my-rhel[a:d].company.com",
                    "my-rhel[120:400].company.com",
                ],
                exclude_hosts=[
                    "10.10.181.9",
                    "10.10.181.8/16",
                    "10.10.[1:20].25",
                    "localhost",
                    "my-rhel[a:d].company.com",
                ],
                type="network",
                port=22,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_ADDED % "source1"
                assert expected_message in caplog.text

    ##################################################
    # Vcenter Source Test
    ##################################################
    def test_add_source_vc(self, caplog):
        """Testing the add vcenter source command successfully."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        cred_results = [{"id": 1, "name": "cred1"}]
        get_cred_data = {"count": 1, "results": cred_results}
        post_source_url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=200, json=get_cred_data)
            mocker.post(post_source_url, status_code=201)

            args = Namespace(
                name="source1", cred=["cred1"], hosts=["1.2.3.4"], type="vcenter"
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_ADDED % "source1"
                assert expected_message in caplog.text

    def test_add_source_with_ssl_params(self, caplog):
        """Testing add vcenter source command with all ssl params."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        cred_results = [{"id": 1, "name": "cred1"}]
        get_cred_data = {"count": 1, "results": cred_results}
        post_source_url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=200, json=get_cred_data)
            mocker.post(post_source_url, status_code=201)

            args = Namespace(
                name="source1",
                cred=["cred1"],
                hosts=["10.10.181.9"],
                ssl_cert_verify="True",
                disable_ssl="False",
                ssl_protocol="SSL_PROTOCOL_SSLv23",
                type="vcenter",
                port=22,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_ADDED % "source1"
                assert expected_message in caplog.text

    ##################################################
    # Satellite Source Test
    ##################################################
    def test_add_source_sat(self, caplog):
        """Testing the add satellite source command successfully."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        cred_results = [{"id": 1, "name": "cred1"}]
        get_cred_data = {"count": 1, "results": cred_results}
        post_source_url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=200, json=get_cred_data)
            mocker.post(post_source_url, status_code=201)

            args = Namespace(
                name="source1", cred=["cred1"], hosts=["1.2.3.4"], type="satellite"
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_ADDED % "source1"
                assert expected_message in caplog.text

    def test_add_source_sat_no_ssl(self, caplog):
        """Testing the add satellite with ssl_cert_verify set to false."""
        get_cred_url = get_server_location() + CREDENTIAL_URI + "?name=cred1"
        cred_results = [{"id": 1, "name": "cred1"}]
        get_cred_data = {"count": 1, "results": cred_results}
        post_source_url = get_server_location() + SOURCE_URI
        with requests_mock.Mocker() as mocker:
            mocker.get(get_cred_url, status_code=200, json=get_cred_data)
            mocker.post(post_source_url, status_code=201)

            args = Namespace(
                name="source1",
                cred=["cred1"],
                hosts=["1.2.3.4"],
                type="satellite",
                ssl_cert_verify="false",
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_ADDED % "source1"
                assert expected_message in caplog.text
