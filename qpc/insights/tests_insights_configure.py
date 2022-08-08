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
import os
import sys

import pytest

from qpc import messages, utils
from qpc.cli import CLI
from qpc.utils import (
    DEFAULT_HOST_INSIGHTS_CONFIG,
    DEFAULT_INSIGHTS_CONFIG,
    DEFAULT_PORT_INSIGHTS_CONFIG,
    DEFAULT_USE_HTTP_INSIGHTS_CONFIG,
    read_insights_config,
    write_insights_config,
    write_server_config,
)


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


class TestInsightsConfigureCommand:
    """Class for testing insights host configuration command."""

    def test_insights_config_bad_port(self):
        """Testing insights configure when receiving bad port."""
        sys.argv = ["/bin/qpc", "insights", "config", "--port", "abc"]
        with pytest.raises(SystemExit):
            CLI().main()

    def test_insights_config_empty_host(self):
        """Testing insights configure when receiving bad host."""
        sys.argv = ["/bin/qpc", "insights", "config", "--host", ""]
        with pytest.raises(SystemExit):
            CLI().main()

    def test_insights_config_bad_host(self):
        """Testing insights configure when receiving bad host."""
        sys.argv = ["/bin/qpc", "insights", "config", "--host", None]
        with pytest.raises(SystemExit):
            CLI().main()

    def test_success_default_config_no_args(self):
        """Testing if method returns default config dict when no arguments."""
        config = read_insights_config()
        assert config == DEFAULT_INSIGHTS_CONFIG
        assert os.path.exists(utils.INSIGHTS_CONFIG) is False

    def test_success_config_insights(self, caplog):
        """Testing insights configure green path."""
        caplog.set_level("INFO")
        sys.argv = [
            "/bin/qpc",
            "insights",
            "config",
            "--host",
            "console.insights.test",
            "--port",
            "200",
            "--use-http",
        ]
        CLI().main()
        config = read_insights_config()
        assert config["host"] == "console.insights.test"
        assert config["port"] == 200
        assert config["use_http"]
        assert caplog.messages[-1] == (
            messages.INSIGHTS_CONFIG_SUCCESS
            % "{'host': 'console.insights.test', 'port': 200, 'use_http': True}"
        )

    def test_insights_config_default_host(self, caplog):
        """Testing insights configure default host."""
        caplog.set_level("INFO")
        sys.argv = ["/bin/qpc", "insights", "config", "--port", "200"]
        CLI().main()
        config = read_insights_config()
        assert config["host"] == DEFAULT_HOST_INSIGHTS_CONFIG
        assert config["port"] == 200
        assert config["use_http"] == DEFAULT_USE_HTTP_INSIGHTS_CONFIG
        assert caplog.messages[-1] == (
            messages.INSIGHTS_CONFIG_SUCCESS
            % "{'host': 'console.redhat.com', 'port': 200, 'use_http': False}"
        )

    def test_insights_config_default_port(self, caplog):
        """Testing insights configure default port."""
        caplog.set_level("INFO")
        sys.argv = ["/bin/qpc", "insights", "config", "--host", "console.insights.test"]
        CLI().main()
        config = read_insights_config()
        assert config["host"] == "console.insights.test"
        assert config["port"] == DEFAULT_PORT_INSIGHTS_CONFIG
        assert config["use_http"] == DEFAULT_USE_HTTP_INSIGHTS_CONFIG
        assert caplog.messages[-1] == (
            messages.INSIGHTS_CONFIG_SUCCESS
            % "{'host': 'console.insights.test', 'port': 443, 'use_http': False}"
        )

    def test_invalid_configuration(self):
        """Test reading bad JSON on cli start."""
        write_insights_config({})

        config = read_insights_config()
        assert config["host"] == DEFAULT_HOST_INSIGHTS_CONFIG
        assert config["port"] == DEFAULT_PORT_INSIGHTS_CONFIG
        assert config["use_http"] == DEFAULT_USE_HTTP_INSIGHTS_CONFIG
