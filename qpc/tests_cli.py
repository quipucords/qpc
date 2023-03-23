"""Test the CLI module."""

import sys
import unittest
from io import StringIO

from qpc.cli import CLI
from qpc.release import VERSION
from qpc.tests_utilities import HushUpStderr, redirect_stdout


class CliTests(unittest.TestCase):
    """Class for testing the base cli arguments for qpc."""

    def setUp(self):
        """Create test setup."""
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        """Tear down test case setup."""
        # Restore stderr
        sys.stderr = self.orig_stderr

    def test_version(self):
        """Testing the verion argument."""
        version_out = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(version_out):
                sys.argv = ["/bin/qpc", "--version"]
                CLI().main()
                self.assertEqual(version_out.getvalue(), VERSION)
