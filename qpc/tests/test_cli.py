"""Test the CLI module."""

import sys
from unittest.mock import patch

import pytest

from qpc import cli
from qpc.release import VERSION


def test_version(capsys):
    """Test the `--version` argument."""
    test_argv = ["/bin/qpc", "--version"]
    with pytest.raises(SystemExit), patch.object(sys, "argv", test_argv):
        cli.CLI().main()
    captured = capsys.readouterr()
    assert captured.out.strip() == VERSION


def test_build_sha(capsys):
    """Test the `--build-sha` argument."""
    test_argv = ["/bin/qpc", "--build-sha"]
    expected_value = "C00010FF"
    with (
        pytest.raises(SystemExit),
        patch.object(sys, "argv", test_argv),
        patch.object(cli, "get_current_sha1") as mock_getter,
    ):
        mock_getter.return_value = expected_value
        cli.CLI().main()
    captured = capsys.readouterr()
    assert captured.out.strip() == expected_value
