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
from qpc.request import CONNECTION_ERROR_MSG
from qpc.scan import SCAN_URI
from qpc.scan.add import ScanAddCommand
from qpc.source import SOURCE_URI
from qpc.tests.utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config


class TestScanAddCli:
    """Class for testing the scan add commands for qpc."""

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = ScanAddCommand(subparser)

    def setup_method(self, _test_method):
        """Create test setup."""
        write_server_config(DEFAULT_CONFIG)
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def teardown_method(self, _test_method):
        """Tear down test case setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_add_req_args_err(self):
        """Testing the scan add command required flags."""
        with pytest.raises(SystemExit):
            sys.argv = ["/bin/qpc", "scan", "add", "--name", "scan1"]
            CLI().main()

    def test_scan_source_none(self):
        """Testing the scan add command for none existing source."""
        scan_out = StringIO()
        url = get_server_location() + SOURCE_URI + "?name=source_none"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, status_code=200, json={"count": 0})

            args = Namespace(sources=["source_none"])
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    self.command.main(args)
                    assert 'Source "source_none" does not exist' in scan_out.getvalue()

    def test_add_scan_ssl_err(self):
        """Testing the add scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.SSLError)

            args = Namespace(sources=["source1"])
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == CONNECTION_ERROR_MSG

    def test_add_scan_conn_err(self):
        """Testing the add scan command with a connection error."""
        scan_out = StringIO()
        url = get_server_location() + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url, exc=requests.exceptions.ConnectTimeout)

            args = Namespace(sources=["source1"])
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == CONNECTION_ERROR_MSG

    def test_add_scan_bad_resp(self):
        """Testing the add scan command with a 500."""
        scan_out = StringIO()
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=500, json=None)

            args = Namespace(sources=["source1"], max_concurrency=50)
            with pytest.raises(SystemExit):
                with redirect_stdout(scan_out):
                    self.command.main(args)
                    assert scan_out.getvalue() == messages.SERVER_INTERNAL_ERROR

    def test_add_scan(self, caplog):
        """Testing the add scan command successfully."""
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        url_post = get_server_location() + SCAN_URI
        results = [
            {
                "id": 1,
                "name": "scan1",
                "sources": ["source1"],
                "disable-optional-products": {
                    "jboss-eap": False,
                    "jboss-fuse": False,
                    "jboss-brms": False,
                },
            }
        ]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.post(url_post, status_code=201, json={"name": "scan1"})

            args = Namespace(
                name="scan1",
                sources=["source1"],
                max_concurrency=50,
                disabled_optional_products={
                    "jboss-eap": False,
                    "jboss-fuse": False,
                    "jboss-brms": False,
                },
                enabled_ext_product_search=None,
                ext_product_search_dirs=None,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SCAN_ADDED % "scan1"
                assert expected_message in caplog.text

    def test_disable_optional_products(self, caplog):
        """Testing that the disable-optional-products flag works correctly."""
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        url_post = get_server_location() + SCAN_URI
        results = [
            {
                "id": 1,
                "name": "scan1",
                "sources": ["source1"],
                "max-concurrency": 4,
                "disabled_optional_products": ["jboss-fuse"],
            }
        ]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.post(url_post, status_code=201, json={"name": "scan1"})

            args = Namespace(
                name="scan1",
                sources=["source1"],
                max_concurrency=50,
                disabled_optional_products={
                    "jboss-eap": True,
                    "jboss-fuse": False,
                    "jboss-brms": True,
                },
                enabled_ext_product_search=None,
                ext_product_search_dirs=None,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SCAN_ADDED % "scan1"
                assert expected_message in caplog.text

    @pytest.mark.parametrize(
        "disable_opt_products_value", ("1", "-100", "redhat_packages", "ifconfig")
    )
    def test_disable_optional_products_negative(
        self, capsys, disable_opt_products_value
    ):
        """Test add scan with unknown disabled-optional-products value."""
        sys.argv = [
            "/bin/qpc",
            "scan",
            "add",
            "--name",
            "scan_1",
            "--sources",
            "source_1",
            "--disabled-optional-products",
            disable_opt_products_value,
        ]
        with pytest.raises(SystemExit):
            CLI().main()

        expected_output = "--disabled-optional-products: invalid choice: '{}'"
        out, err = capsys.readouterr()
        assert out == ""
        assert expected_output.format(disable_opt_products_value) in err

    def test_enabled_products_and_dirs(self, caplog):
        """Testing that the ext products & search dirs flags work correctly."""
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        url_post = get_server_location() + SCAN_URI
        results = [
            {
                "id": 1,
                "name": "scan1",
                "sources": ["source1"],
                "max-concurrency": 4,
                "enabled_extended_product_search": {
                    "jboss-eap": True,
                    "jboss-fuse": False,
                    "jboss-brms": True,
                    "search_directories": ["/foo/bar/"],
                },
            }
        ]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.post(url_post, status_code=201, json={"name": "scan1"})

            args = Namespace(
                name="scan1",
                sources=["source1"],
                max_concurrency=50,
                disabled_optional_products=None,
                enabled_ext_product_search=["jboss-eap", "jboss-brms"],
                ext_product_search_dirs="/foo/bar/",
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SCAN_ADDED % "scan1"
                assert expected_message in caplog.text

    def test_enabled_products_only(self, caplog):
        """Testing that the enabled-ext-product-search flag works."""
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        url_post = get_server_location() + SCAN_URI
        results = [
            {
                "id": 1,
                "name": "scan1",
                "sources": ["source1"],
                "max-concurrency": 4,
                "enabled_extended_product_search": {
                    "jboss_eap": True,
                    "jboss_fuse": False,
                    "jboss_brms": True,
                },
            }
        ]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.post(url_post, status_code=201, json={"name": "scan1"})

            args = Namespace(
                name="scan1",
                sources=["source1"],
                max_concurrency=50,
                disabled_optional_products=None,
                enabled_ext_product_search=["jboss_eap", "jboss_brms"],
                ext_product_search_dirs=None,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SCAN_ADDED % "scan1"
                assert expected_message in caplog.text

    @pytest.mark.parametrize(
        "enabled_ext_products_value", ("1", "-100", "redhat_packages", "ifconfig")
    )
    def test_enabled_ext_products_negative(self, capsys, enabled_ext_products_value):
        """Test add scan with unknown enabled-ext-product-search value."""
        sys.argv = [
            "/bin/qpc",
            "scan",
            "add",
            "--name",
            "scan_1",
            "--sources",
            "source_1",
            "--enabled-ext-product-search",
            enabled_ext_products_value,
        ]
        with pytest.raises(SystemExit):
            CLI().main()

        expected_output = "--enabled-ext-product-search: invalid choice: '{}'"
        out, err = capsys.readouterr()
        assert out == ""
        assert expected_output.format(enabled_ext_products_value) in err

    def test_disable_optional_products_empty(self, caplog):
        """Testing that the disable-optional-products flag works correctly."""
        url_get_source = get_server_location() + SOURCE_URI + "?name=source1"
        url_post = get_server_location() + SCAN_URI
        results = [{"id": 1, "name": "scan1", "sources": ["source1"]}]
        source_data = {"count": 1, "results": results}
        with requests_mock.Mocker() as mocker:
            mocker.get(url_get_source, status_code=200, json=source_data)
            mocker.post(url_post, status_code=201, json={"name": "scan1"})

            args = Namespace(
                name="scan1",
                sources=["source1"],
                max_concurrency=50,
                disabled_optional_products=None,
                enabled_ext_product_search=None,
                ext_product_search_dirs=None,
            )
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                expected_message = messages.SCAN_ADDED % "scan1"
                assert expected_message in caplog.text
