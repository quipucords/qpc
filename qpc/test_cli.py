"""Test the CLI module."""

import sys
from unittest.mock import patch

import pytest

from qpc.cli import CLI
from qpc.release import VERSION


def test_version(capsys):
    """Test the `--version` argument."""
    test_argv = ["/bin/qpc", "--version"]
    with pytest.raises(SystemExit), patch.object(sys, "argv", test_argv):
        CLI().main()
    captured = capsys.readouterr()
    assert captured.out.strip() == VERSION
