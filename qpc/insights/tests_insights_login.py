"""Test the CLI module."""

import sys

from qpc.cli import CLI


class TestInsightsLogin:
    """Class for testing insights login command."""

    def test_insight_login(self, capsys):
        """Testing if insights login command requires args."""
        sys.argv = ["/bin/qpc", "insights", "login"]
        CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert err == ""
