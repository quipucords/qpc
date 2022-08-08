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
from qpc.utils import read_insights_login_config, write_server_config


@pytest.fixture(autouse=True)
def _setup_server_config_file():
    """
    Create server config with require_token set to False.

    Since all cli commands require qpc config and qpc login to be executed,
    require_token must be False, to avoid passing login info
    """
    return write_server_config(
        {
            "host": "127.0.0.1",
            "port": 8000,
            "use_http": True,
            "require_token": False,
        }
    )


class TestInsightsAddLoginCommand:
    """Class for testing insights add login command."""

    def test_insight_login_req_args_err(self):
        """Testing if insights add-login command requires args."""
        sys.argv = ["/bin/qpc", "insights", "add_login"]
        with pytest.raises(SystemExit):
            CLI().main()

    def test_insights_config_bad_username(self):
        """Testing insights configure when receiving bad username."""
        sys.argv = ["/bin/qpc", "insights", "add-login", "--username", None]
        with pytest.raises(SystemExit):
            CLI().main()

    def test_insights_config_empty_username(self):
        """Testing insights configure when receiving bad username."""
        sys.argv = ["/bin/qpc", "insights", "add-login", "--username", ""]
        with pytest.raises(SystemExit):
            CLI().main()

    def test_insights_config_bad_password(self):
        """Testing insights configure when receiving bad username."""
        sys.argv = ["/bin/qpc", "insights", "add-login", "--password", None]
        with pytest.raises(SystemExit):
            CLI().main()

    def test_insights_config_empty_password(self):
        """Testing insights configure when receiving bad username."""
        sys.argv = ["/bin/qpc", "insights", "add-login", "--password", ""]
        with pytest.raises(SystemExit):
            CLI().main()

    def test_success_add_insights_login_config(self, caplog):
        """Testing insights login config green path."""
        caplog.set_level("INFO")
        sys.argv = [
            "/bin/qpc",
            "insights",
            "add_login",
            "--username",
            "insights-test-user",
            "--password",
            "insights-test-password",
        ]
        CLI().main()
        config = read_insights_login_config()
        assert config["username"] == "insights-test-user"
        assert config["password"] == "insights-test-password"
        assert caplog.messages[-1] == messages.INSIGHTS_LOGIN_CONFIG_SUCCESS

    def test_run_command_no_config(self):
        """Test running command without config."""
        sys.argv = ["/bin/qpc", "insights", "add_login"]
        with pytest.raises(SystemExit):
            CLI().main()
