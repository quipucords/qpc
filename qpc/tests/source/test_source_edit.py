"""Test the CLI module."""

import logging
import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest
import requests
import requests_mock

from qpc import messages
from qpc.cli import CLI
from qpc.cred import CREDENTIAL_URI
from qpc.request import CONNECTION_ERROR_MSG
from qpc.source import SOURCE_URI
from qpc.source.edit import SourceEditCommand
from qpc.tests.utilities import redirect_stdout
from qpc.utils import get_server_location, read_in_file


@pytest.fixture
def hostsfile(tmp_path):
    """Return the path to a hostsfile for testing."""
    _file = tmp_path / "hostsfile"
    _file.write_text("1.2.3.4\n1.2.3.[1:10]\n")
    return str(_file)


@pytest.mark.usefixtures("server_config")
class TestSourceEditCli:
    """Class for testing the source edit commands for qpc."""

    def _init_command(self):
        """Return command with argument parser properly initialized."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        return SourceEditCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        # different from most other test cases where command is initialized once per
        # class, this one requires to be initialized for each test method because
        # SourceEditCommand instance modifies req_path on the fly. This seems to be a
        # code smell to me, but I'm choosing to ignore it for now
        self.command = self._init_command()

    def test_edit_req_args_err(self):
        """Testing the add edit command required flags."""
        source_out = StringIO()
        with pytest.raises(SystemExit):
            with redirect_stdout(source_out):
                sys.argv = ["/bin/qpc", "source", "edit", "--name", "source1"]
                CLI().main()
                assert (
                    source_out.getvalue()
                    == "No arguments provided to edit source source1"
                )

    def test_edit_process_file(self, hostsfile):
        """Testing the add source command process file."""
        with pytest.raises(SystemExit):
            sys.argv = [
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
                "credential1",
            ]
            CLI().main()

    def test_read_input(self, hostsfile):
        """Test the input reading mechanism."""
        vals = read_in_file(hostsfile)
        expected = ["1.2.3.4", "1.2.3.[1:10]"]
        assert expected == vals

    def test_edit_source_none(self):
        """Testing the edit cred command for none existing cred."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI + "?name=source_none"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})
            args = Namespace(
                name="source_none", hosts=["1.2.3.4"], cred=["credential1"], port=22
            )
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    self.command.main(args)
                    assert (
                        'Source "source_none" does not exist' in source_out.getvalue()
                    )

    def test_edit_source_ssl_err(self):
        """Testing the edit source command with a connection error."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)
            args = Namespace(
                name="source1", hosts=["1.2.3.4"], cred=["credential1"], port=22
            )
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == CONNECTION_ERROR_MSG

    def test_edit_source_conn_err(self):
        """Testing the edit source command with a connection error."""
        source_out = StringIO()
        url = get_server_location() + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)

            args = Namespace(
                name="source1", hosts=["1.2.3.4"], cred=["credential1"], port=22
            )
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == CONNECTION_ERROR_MSG

    ##################################################
    # Network Source Test
    ##################################################
    def test_edit_net_source(self, caplog):
        """Testing the edit network source command successfully."""
        url_get_cred = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        url_patch = get_server_location() + SOURCE_URI + "1/"
        cred_results = [{"id": 1, "name": "credential1", "username": "root"}]
        cred_data = {"count": 1, "results": cred_results}
        results = [
            {
                "id": 1,
                "name": "source1",
                "hosts": ["1.2.3.4"],
                "exclude_hosts": ["1.2.3.4."],
                "credentials": [{"id": 2, "name": "cred2"}],
            }
        ]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            mocker.patch(url_patch, status_code=200)

            args = Namespace(
                name="source1",
                hosts=["1.2.3.4", "2.3.4.5"],
                excluded_hosts=["1.2.3.4"],
                cred=["credential1"],
                port=22,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_UPDATED % "source1"
                assert expected_message in caplog.text

    def test_edit_source_exclude_host(self, caplog):
        """Testing edit network source command by adding an excluded host."""
        url_get_cred = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        url_patch = get_server_location() + SOURCE_URI + "1/"
        cred_results = [{"id": 1, "name": "credential1", "username": "root"}]
        cred_data = {"count": 1, "results": cred_results}
        results = [
            {
                "id": 1,
                "name": "source1",
                "hosts": ["1.2.3.4"],
                "credentials": [{"id": 2, "name": "cred2"}],
            }
        ]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            mocker.patch(url_patch, status_code=200)

            args = Namespace(
                name="source1",
                hosts=["1.2.3.[0:255]"],
                exclude_hosts=["1.2.3.4"],
                cred=["credential1"],
                port=22,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_UPDATED % "source1"
                assert expected_message in caplog.text

    ##################################################
    # Vcenter Source Test
    ##################################################
    def test_edit_vc_source(self, caplog):
        """Testing the edit vcenter source command successfully."""
        url_get_cred = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        url_patch = get_server_location() + SOURCE_URI + "1/"
        cred_results = [{"id": 1, "name": "credential1", "username": "root"}]
        cred_data = {"count": 1, "results": cred_results}
        results = [
            {
                "id": 1,
                "name": "source1",
                "hosts": ["1.2.3.4"],
                "credentials": [{"id": 2, "name": "cred2"}],
            }
        ]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            mocker.patch(url_patch, status_code=200)

            args = Namespace(name="source1", hosts=["1.2.3.5"], cred=["credential1"])
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_UPDATED % "source1"
                assert expected_message in caplog.text

    def test_edit_disable_ssl(self, caplog):
        """Testing that you can edit the disable-ssl arg successfully."""
        url_get_cred = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        url_patch = get_server_location() + SOURCE_URI + "1/"
        cred_results = [{"id": 1, "name": "credential1", "username": "root"}]
        cred_data = {"count": 1, "results": cred_results}
        results = [
            {
                "id": 1,
                "name": "source1",
                "hosts": ["1.2.3.4"],
                "credentials": [{"id": 2, "name": "cred2"}],
                "disable_ssl": "false",
            }
        ]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            mocker.patch(url_patch, status_code=200)

            args = Namespace(
                name="source1",
                hosts=["1.2.3.5"],
                cred=["credential1"],
                disable_ssl="True",
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_UPDATED % "source1"
                assert expected_message in caplog.text

    def test_edit_ssl_protocol(self, caplog):
        """Testing that you can edit the ssl_protocol arg successfully."""
        url_get_cred = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        url_patch = get_server_location() + SOURCE_URI + "1/"
        cred_results = [{"id": 1, "name": "credential1", "username": "root"}]
        cred_data = {"count": 1, "results": cred_results}
        results = [
            {
                "id": 1,
                "name": "source1",
                "hosts": ["1.2.3.4"],
                "credentials": [{"id": 2, "name": "cred2"}],
                "ssl_protocol": "SSLv23",
            }
        ]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            mocker.patch(url_patch, status_code=200)

            args = Namespace(
                name="source1",
                hosts=["1.2.3.5"],
                cred=["credential1"],
                ssl_protocol="SSLv23",
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SOURCE_UPDATED % "source1"
                assert expected_message in caplog.text

    def test_edit_source_no_val(self):
        """Testing the edit source command with a server error."""
        source_out = StringIO()
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=500, json=None)

            args = Namespace(
                name="source1", hosts=["1.2.3.4"], cred=["credential1"], port=22
            )
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert source_out.getvalue() == messages.SERVER_INTERNAL_ERROR

    def test_edit_source_cred_nf(self):
        """Testing the edit source command where cred is not found."""
        source_out = StringIO()
        url_get_cred = (
            get_server_location() + CREDENTIAL_URI + "?name=credential1%2Ccred2"
        )
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        cred_results = [{"id": 1, "name": "credential1", "username": "root"}]
        cred_data = {"count": 1, "results": cred_results}
        results = [
            {
                "id": 1,
                "name": "source1",
                "hosts": ["1.2.3.4"],
                "credentials": [{"id": 2, "name": "cred2"}],
            }
        ]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)

            args = Namespace(
                name="source1",
                hosts=["1.2.3.4"],
                cred=["credential1", "cred2"],
                port=22,
            )
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert (
                        'An error occurred while processing the "--cred" input'
                        in source_out.getvalue()
                    )

    def test_edit_source_cred_err(self):
        """Testing the edit source command where cred request hits error."""
        source_out = StringIO()
        url_get_cred = (
            get_server_location() + CREDENTIAL_URI + "?name=credential1%2Ccred2"
        )
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        results = [
            {
                "id": 1,
                "name": "source1",
                "hosts": ["1.2.3.4"],
                "credentials": [{"id": 2, "name": "cred2"}],
            }
        ]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=500)

            args = Namespace(
                name="source1",
                hosts=["1.2.3.4"],
                cred=["credential1", "cred2"],
                port=22,
            )
            with pytest.raises(SystemExit):
                with redirect_stdout(source_out):
                    self.command.main(args)
                    assert (
                        'An error occurred while processing the "--cred" input'
                        in source_out.getvalue()
                    )

    @pytest.mark.skip(
        reason=(
            "FIXME! qpc.source.utils::validate_port explicitly allows port=0. "
            "However, since 0 is False when used in boolean context, "
            "`build_source_payload()` will always ignore it, and "
            "`SourceEditCommand._validate_args()` will ignore it if --port is "
            "only argument."
        )
    )
    def test_edit_source_port_0(self, caplog):
        """Make sure that editing source to set port to 0 works."""
        url_get_cred = get_server_location() + CREDENTIAL_URI + "?name=credential1"
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        url_patch = get_server_location() + SOURCE_URI + "1/"
        cred_results = [{"id": 1, "name": "credential1", "username": "root"}]
        cred_data = {"count": 1, "results": cred_results}
        results = [
            {
                "id": 1,
                "name": "source1",
                "hosts": ["1.2.3.4"],
                "credentials": [{"id": 1, "name": "credential1"}],
            }
        ]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.get(url_get_cred, status_code=200, json=cred_data)
            mocker.patch(url_patch, status_code=200)

            with caplog.at_level(logging.INFO):
                sys.argv = [
                    "/bin/qpc",
                    "source",
                    "edit",
                    "--name",
                    "source1",
                    "--port",
                    "0",
                ]
                CLI().main()
                expected_message = messages.SOURCE_UPDATED % "source1"
                assert expected_message in caplog.text
