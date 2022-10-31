# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the CLI module."""

import sys

import pytest

from qpc import messages
from qpc.cli import CLI
from qpc.utils import read_insights_login_config


class TestInsightsAddLogin:
    """Class for testing insights add login command."""

    def test_insight_login_req_args_err(self, capsys):
        """Testing if insights add-login command requires args."""
        sys.argv = ["/bin/qpc", "insights", "add_login"]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        expected_error = (
            "error: the following arguments are required: --username, --password"
        )
        assert out == ""
        assert expected_error in err

    def test_insights_config_bad_username(self, capsys):
        """Testing insights configure when receiving bad username."""
        sys.argv = ["/bin/qpc", "insights", "add_login", "--username", None]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        expected_error = "invalid validate_username_and_password value: None"
        assert out == ""
        assert expected_error in err

    def test_insights_config_empty_username(self, capsys):
        """Testing insights configure when receiving empty username."""
        sys.argv = ["/bin/qpc", "insights", "add_login", "--username", ""]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        expected_error = "error: argument --username: The argument value is invalid."
        assert out == ""
        assert expected_error in err

    def test_insights_config_bad_password(self):
        """Testing insights configure when receiving bad password."""
        sys.argv = [
            "/bin/qpc",
            "insights",
            "add_login",
            "--username",
            "test_username",
            "--password",
            None,
        ]
        with pytest.raises(TypeError):
            CLI().main()

    def test_insights_config_empty_password(self, capsys):
        """Testing insights configure when receiving empty password."""
        sys.argv = [
            "/bin/qpc",
            "insights",
            "add_login",
            "--username",
            "test-username",
            "--password",
            "",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        expected_error = "qpc: error: unrecognized arguments: "
        assert out == ""
        assert expected_error in err

    def test_success_add_insights_login_config(
        self, insights_login_password_input, caplog
    ):
        """Testing insights login config green path."""
        caplog.set_level("INFO")
        sys.argv = [
            "/bin/qpc",
            "insights",
            "add_login",
            "--username",
            "insights-test-user",
            "--password",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.INSIGHTS_LOGIN_CONFIG_SUCCESS
        config = read_insights_login_config()
        assert config["username"] == "insights-test-user"
        assert config["password"] == "insights-test-password"

    def test_run_command_no_config(self):
        """Test running command without config."""
        sys.argv = ["/bin/qpc", "insights", "add_login"]
        with pytest.raises(SystemExit):
            CLI().main()
