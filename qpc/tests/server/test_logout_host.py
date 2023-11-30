"""Test the CLI module."""

import sys
from argparse import ArgumentParser, Namespace

import requests_mock

from qpc import utils
from qpc.server import LOGOUT_URI
from qpc.server.logout_host import LogoutHostCommand
from qpc.tests.utilities import HushUpStderr


class TestLogout:
    """Class for testing the logout host function."""

    def setup_class(cls):
        """Set up test case."""
        argument_parser = ArgumentParser()
        subparser = argument_parser.add_subparsers(dest="subcommand")
        cls.command = LogoutHostCommand(subparser)

    def setup_method(self, _method):
        """Create test setup."""
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()
        utils.write_server_config({"host": "127.0.0.1", "port": 8000, "use_http": True})

    def teardown_method(self, _method):
        """Remove test case setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_success_logout(self):
        """Testing the logout server green path."""
        url = utils.get_server_location() + LOGOUT_URI
        with requests_mock.Mocker() as mocker:
            mocker.put(url, status_code=200)
            args = Namespace()
            self.command.main(args)
            assert not utils.QPC_CLIENT_TOKEN.exists()
