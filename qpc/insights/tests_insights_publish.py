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
import tempfile
from unittest import mock

import pytest

from qpc import messages
from qpc.cli import CLI
from qpc.insights import INGRESS_REPORT_URI
from qpc.utils import write_server_config


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


@pytest.fixture
def patched_insights_config():
    """Mock insights config file values."""
    config = {
        "host": "insights.test",
        "port": 1111,
        "use_http": False,
    }

    with mock.patch(
        "qpc.insights.publish.read_insights_config", return_value=config
    ) as patched_config:
        yield patched_config


@pytest.fixture
def patched_insights_credentials():
    """Mock insights login config file values."""
    credentials = {
        "username": "john_doe",
        "password": "shadowman",
    }

    with mock.patch(
        "qpc.insights.publish.read_insights_login_config", return_value=credentials
    ) as patched_credentials:
        yield patched_credentials


@pytest.fixture
def inapropriate_payload_file():
    """Temp file with inappropriate extension for testing purposes."""
    tmp_file = tempfile.NamedTemporaryFile(  # pylint: disable=consider-using-with
        suffix=".json"
    )
    yield tmp_file
    tmp_file.close()


@pytest.fixture
def payload_file():
    """Temp file with .tar.gz extension for testing purposes."""
    tmp_file = tempfile.NamedTemporaryFile(  # pylint: disable=consider-using-with
        suffix=".tar.gz"
    )
    yield tmp_file
    tmp_file.close()


class TestInsightsPublishCommand:
    """Class for testing insights publish command."""

    def test_insight_login_req_args_err(self):
        """Testing if insights publish command requires args."""
        sys.argv = ["/bin/qpc", "insights", "publish"]
        with pytest.raises(SystemExit):
            CLI().main()

    def test_validate_report_name_if_invalid_name(
        self,
        inapropriate_payload_file: tempfile.NamedTemporaryFile,
        caplog,
    ):
        """Testing if--input-file will accept files with inappropriate extensions."""
        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--input-file",
            inapropriate_payload_file.name,
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        assert caplog.messages[-1] == messages.INSIGHTS_LOCAL_REPORT_NOT_TAR_GZ

    def test_validate_report_name_if_not_file(self, tmp_path, caplog):
        """Testing if insights publish --input-file will accept dir as file."""
        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--input-file",
            tmp_path.name,
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        assert caplog.messages[-1] == messages.INSIGHTS_LOCAL_REPORT_NOT

    def test_insights_publish_successful(  # pylint: disable=too-many-arguments
        self,
        payload_file,
        patched_insights_config,
        patched_insights_credentials,
        caplog,
        requests_mock,
    ):
        """Testing insights publish --input-file green path."""
        requests_mock.post(
            f"https://insights.test:1111{INGRESS_REPORT_URI}",
            status_code=202,
        )
        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--input-file",
            payload_file.name,
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.INSIGHTS_PUBLISH_SUCCESSFUL

    @pytest.mark.parametrize(
        "status_code,log_message",
        [
            (401, messages.INSIGHTS_PUBLISH_AUTH_ERROR),
            (404, messages.INSIGHTS_PUBLISH_NOT_FOUND_ERROR),
            (500, messages.INSIGHTS_PUBLISH_INTERNAL_SERVER_ERROR),
        ],
    )
    def test_insights_publish_returning_error(  # pylint: disable=too-many-arguments
        self,
        payload_file,
        patched_insights_config,
        patched_insights_credentials,
        caplog,
        requests_mock,
        status_code,
        log_message,
    ):
        """Testing insights publish with several errors."""
        requests_mock.post(
            f"https://insights.test:1111{INGRESS_REPORT_URI}",
            status_code=status_code,
        )
        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--input-file",
            payload_file.name,
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        assert caplog.messages[-1] == log_message
