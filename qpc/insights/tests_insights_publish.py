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
from qpc.insights import INGRESS_REPORT_URI, INSIGHTS_PATH_SUFFIX, REPORT_URI
from qpc.insights.publish import InsightsPublishCommand


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

    def test_insights_publish_req_args_err(self):
        """Testing if insights publish command requires args."""
        sys.argv = ["/bin/qpc", "insights", "publish"]
        with pytest.raises(SystemExit):
            CLI().main()

    def test_insights_publish_args_are_mutually_exclusive(self, mocker):
        """Testing if insights publish command args are mutually exclusive."""
        mocker.patch.object(
            InsightsPublishCommand, "_publish_to_ingress", side_effect=RuntimeError()
        )
        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--input-file",
            "file_example",
            "--report",
            "1",
        ]
        with pytest.raises(SystemExit) as exc_info:
            CLI().main()
        # argparse will always exit with value 2
        assert exc_info.value.code == 2

    def test_validate_report_name_if_invalid_name(
        self,
        inapropriate_payload_file: tempfile.NamedTemporaryFile,
        caplog,
    ):
        """Testing if--input-file will accept files with inappropriate extensions."""
        caplog.set_level("ERROR")
        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--input-file",
            inapropriate_payload_file.name,
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        assert (
            caplog.messages[-1]
            == messages.INSIGHTS_LOCAL_REPORT_NOT_TAR_GZ
            % inapropriate_payload_file.name
        )

    def test_validate_report_name_if_not_file(self, tmp_path, caplog):
        """Testing if insights publish --input-file will accept dir as file."""
        caplog.set_level("ERROR")
        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--input-file",
            tmp_path.name,
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        assert caplog.messages[-1] == messages.INSIGHTS_LOCAL_REPORT_NOT % tmp_path.name

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
        assert payload_file.exists(), "Input file should not be removed."

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
        assert payload_file.exists(), "Input file should not be removed."

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

    def test_publish_download_successful(  # pylint: disable=too-many-arguments
        self,
        mocker,
        payload_file,
        patched_insights_credentials,
        caplog,
        requests_mock,
    ):
        """Testing successful report id download from insights publish."""
        caplog.set_level("INFO")
        mocker.patch.object(
            InsightsPublishCommand, "_make_publish_request", return_value=True
        )
        requests_mock.request(
            method="GET",
            url=REPORT_URI + "1" + INSIGHTS_PATH_SUFFIX,
            status_code=200,
            content=payload_file.read_bytes(),
        )

        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--report",
            "1",
        ]
        CLI().main()
        assert caplog.messages[-1] == messages.INSIGHTS_REPORT_DOWNLOAD_SUCCESSFUL

    @pytest.mark.parametrize(
        "status_code, error_message",
        [
            (401, (messages.SERVER_LOGIN_REQUIRED % "qpc")),
            (404, (messages.DOWNLOAD_NO_REPORT_FOUND % "1")),
            (500, messages.SERVER_INTERNAL_ERROR),
        ],
    )
    def test_insights_publish_download_error(  # pylint: disable=too-many-arguments
        self,
        caplog,
        requests_mock,
        status_code,
        error_message,
    ):
        """Testing errors in download for insights publish."""
        caplog.set_level("ERROR")
        requests_mock.request(
            method="GET",
            url=f"{REPORT_URI}1{INSIGHTS_PATH_SUFFIX}",
            status_code=status_code,
        )
        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--report",
            "1",
        ]
        with pytest.raises(SystemExit):
            CLI().main()
        assert caplog.messages[-1] == error_message

    def test_if_file_is_successfully_created_and_deleted(
        self,
        mocker,
        caplog,
        patched_insights_credentials,
        payload_file,
    ):
        """Testing if file created during report download is deleted after published."""
        caplog.set_level("INFO")
        mocker.patch.object(
            InsightsPublishCommand,
            "_download_insights_report",
            return_value=str(payload_file),
        )
        mock_validate_report_name = mocker.patch.object(
            InsightsPublishCommand, "_validate_insights_report_name"
        )
        mock_validate_report_content = mocker.patch.object(
            InsightsPublishCommand, "_validate_insights_report_content"
        )
        mocker.patch.object(
            InsightsPublishCommand, "_make_publish_request", return_value=True
        )

        sys.argv = [
            "/bin/qpc",
            "insights",
            "publish",
            "--report",
            "1",
        ]
        CLI().main()

        mock_validate_report_name.assert_called_with(str(payload_file))
        mock_validate_report_content.assert_called_with(str(payload_file))

        assert not payload_file.exists()
