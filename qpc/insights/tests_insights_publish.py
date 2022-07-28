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
import tarfile
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


def _create_report_tarball(tmp_path, filenames):
    tarball_path = tmp_path / "report.tar.gz"
    with tarfile.open(tarball_path, "w") as tarball:
        for filename in filenames:
            payload = tmp_path / filename
            payload.parent.mkdir(exist_ok=True)
            payload.touch()
            tarball.add(payload, filename)
    return tarball_path


@pytest.fixture
def payload_file(tmp_path):
    """Temp file with .tar.gz extension for testing purposes."""
    yield _create_report_tarball(
        tmp_path, ["report_1/metadata.json", "report_1/asdf.json"]
    )


@pytest.fixture
def payload_without_metadata(tmp_path):
    """Imcomplete payload for testing."""
    yield _create_report_tarball(
        tmp_path, ["report_1/qwert.json", "report_1/asdf.json"]
    )


@pytest.fixture
def payload_with_non_json_file(tmp_path):
    """Payload with unexpected file."""
    yield _create_report_tarball(
        tmp_path, ["report_1/deployments.csv", "report_1/metadata.json"]
    )


@pytest.fixture
def empty_payload(tmp_path):
    """Payload without content."""
    yield _create_report_tarball(tmp_path, [])


@pytest.fixture
def unexpected_payload(tmp_path):
    """Payload unexpected content."""
    yield _create_report_tarball(
        tmp_path, ["report_1/metadata.json", "report_2/asdf.json"]
    )


@pytest.fixture
def non_tarball_payload(tmp_path):
    """Return a non tarball file with tar.gz extension."""
    payload = tmp_path / "report.tar.gz"
    payload.touch()
    yield payload


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
        caplog.set_level("INFO")
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
        caplog.set_level("INFO")
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
        caplog.set_level("INFO")
        requests_mock.post(
            f"https://insights.test:1111{INGRESS_REPORT_URI}",
            status_code=202,
        )
        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--input-file",
            str(payload_file),
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
        caplog.set_level("ERROR")
        requests_mock.post(
            f"https://insights.test:1111{INGRESS_REPORT_URI}",
            status_code=status_code,
        )
        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--input-file",
            str(payload_file),
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        assert caplog.messages[-1] == log_message

    @pytest.mark.parametrize(
        "payload,log_message",
        [
            (
                pytest.lazy_fixture("empty_payload"),
                messages.INSIGHTS_REPORT_CONTENT_MIN_NUMBER,
            ),
            (
                pytest.lazy_fixture("payload_with_non_json_file"),
                messages.INSIGHTS_REPORT_CONTENT_NOT_JSON,
            ),
            (
                pytest.lazy_fixture("payload_without_metadata"),
                messages.INSIGHTS_REPORT_CONTENT_MISSING_METADATA,
            ),
            (
                pytest.lazy_fixture("unexpected_payload"),
                messages.INSIGHTS_REPORT_CONTENT_UNEXPECTED,
            ),
            (
                pytest.lazy_fixture("non_tarball_payload"),
                messages.INSIGHTS_REPORT_CONTENT_UNEXPECTED,
            ),
        ],
    )
    def test_invalid_payload_file(self, payload, caplog, log_message):
        """Test invalid tar.gz payloads."""
        caplog.set_level("INFO")
        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--input-file",
            str(payload),
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        assert caplog.messages[-1] == log_message
