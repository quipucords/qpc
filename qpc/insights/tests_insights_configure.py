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

from qpc import utils
from qpc.cli import CLI
from qpc.utils import (
    DEFAULT_HOST_INSIGHTS_CONFIG,
    DEFAULT_INSIGHTS_CONFIG,
    DEFAULT_PORT_INSIGHTS_CONFIG,
    DEFAULT_USE_HTTP_INSIGHTS_CONFIG,
    read_insights_config,
    write_insights_config,
)


class TestInsightsConfigure:
    """Class for testing insights host configuration."""

    def test_insights_config_bad_port(self):
        """Testing insights configure when receiving bad port."""
        sys.argv = ["/bin/qpc", "insights", "config", "--port", "abc"]
        with pytest.raises(SystemExit):
            CLI().main()

    def test_insights_config_empty_host(self):
        """Testing insights configure when receiving empty host."""
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
        assert not os.path.exists(utils.INSIGHTS_CONFIG)

    def test_success_config_insights(self):
        """Testing insights configure green path."""
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

    def test_insights_config_default_host(self):
        """Testing insights configure default host."""
        sys.argv = ["/bin/qpc", "insights", "config", "--port", "200"]
        CLI().main()
        config = read_insights_config()
        assert config["host"] == DEFAULT_HOST_INSIGHTS_CONFIG
        assert config["port"] == 200
        assert config["use_http"] == DEFAULT_USE_HTTP_INSIGHTS_CONFIG

    def test_insights_config_default_port(self):
        """Testing insights configure default port."""
        sys.argv = ["/bin/qpc", "insights", "config", "--host", "console.insights.test"]
        CLI().main()
        config = read_insights_config()
        assert config["host"] == "console.insights.test"
        assert config["port"] == DEFAULT_PORT_INSIGHTS_CONFIG
        assert config["use_http"] == DEFAULT_USE_HTTP_INSIGHTS_CONFIG

    def test_invalid_configuration(self):
        """Test reading bad JSON on cli start."""
        write_insights_config({})

        config = read_insights_config()
        assert config["host"] == DEFAULT_HOST_INSIGHTS_CONFIG
        assert config["port"] == DEFAULT_PORT_INSIGHTS_CONFIG
        assert config["use_http"] == DEFAULT_USE_HTTP_INSIGHTS_CONFIG
