"""InsightsPublishCommand is used to publish insights report to C.RH.C."""

import sys
import tarfile
from logging import getLogger
from pathlib import Path
from tempfile import NamedTemporaryFile

from qpc import insights, messages
from qpc.clicommand import CliCommand
from qpc.exceptions import QPCError
from qpc.insights.http import InsightsClient
from qpc.request import GET
from qpc.request import request as qpc_request
from qpc.translation import _
from qpc.utils import read_insights_config, read_insights_login_config

logger = getLogger(__name__)


class InsightsPublishCommand(CliCommand):
    """Defines the Insights command.

    This command is for publishing server reports to insights client
    """

    SUBCOMMAND = insights.SUBCOMMAND
    ACTION = insights.PUBLISH

    def __init__(self, subparsers):
        """Create command."""
        super().__init__(
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            None,
            None,
            [],
        )
        id_group = self.parser.add_mutually_exclusive_group(required=True)
        id_group.add_argument(
            "--input-file",
            dest="input_file",
            metavar="INPUT_FILE",
            help=_(messages.INSIGHTS_INPUT_GZIP_HELP),
        )
        id_group.add_argument(
            "--report",
            dest="report",
            type=int,
            metavar="REPORT",
            help=_(messages.REPORT_REPORT_ID_HELP),
        )

    def _validate_insights_report_name(self, input_file: Path):
        """Validate if report file exists and its file extension (tar.gz)."""
        if not input_file.is_file():
            logger.error(_(messages.INSIGHTS_LOCAL_REPORT_NOT), input_file)
            sys.exit(1)
        if not input_file.name.endswith("tar.gz"):
            logger.error(_(messages.INSIGHTS_LOCAL_REPORT_NOT_TAR_GZ), input_file)
            sys.exit(1)

    def _validate_insights_report_content(self, input_file: Path):
        """Check if report tarball contains the expected json files."""
        filenames = self._get_filenames(input_file)

        if len(filenames) < 2:
            logger.error(_(messages.INSIGHTS_REPORT_CONTENT_MIN_NUMBER))
            raise SystemExit(1)

        top_folder, filenames = self._separate_top_folder(filenames)

        if f"{top_folder}/metadata.json" not in filenames:
            logger.error(_(messages.INSIGHTS_REPORT_CONTENT_MISSING_METADATA))
            raise SystemExit(1)

        for filename in filenames:
            self._validate_filename(top_folder, filename)

    def _get_filenames(self, input_file):
        try:
            with tarfile.open(input_file) as tarball:
                filenames = sorted(tarball.getnames())
        except tarfile.ReadError as err:
            logger.exception(_(messages.INSIGHTS_REPORT_CONTENT_UNEXPECTED))
            raise SystemExit(1) from err
        return filenames

    def _is_top_folder(self, top_folder):
        expected_top_folder_parent = Path()
        return top_folder.parent == expected_top_folder_parent

    def _separate_top_folder(self, filenames):
        top_folder = Path(filenames[0])
        if self._is_top_folder(top_folder) and len(filenames) >= 3:
            filenames = filenames[1:]
        elif self._is_top_folder(top_folder.parent):
            top_folder = top_folder.parent
        else:
            logger.error(_(messages.INSIGHTS_REPORT_CONTENT_UNEXPECTED))
            raise SystemExit(1)
        return top_folder, filenames

    def _validate_filename(self, top_folder, filename):
        filepath = Path(filename)
        if filepath.parent != top_folder:
            logger.error(_(messages.INSIGHTS_REPORT_CONTENT_UNEXPECTED))
            raise SystemExit(1)
        if filepath.suffix != ".json":
            logger.error(_(messages.INSIGHTS_REPORT_CONTENT_NOT_JSON))
            raise SystemExit(1)

    def _remove_file_extension(self, input_file):
        file_name = Path(input_file).stem
        return file_name.replace(".tar", "")

    def _publish_to_ingress(self):
        if self.args.input_file:
            input_file = Path(self.args.input_file)
        else:
            input_file = self._download_insights_report()
        self._validate_insights_report_name(input_file)
        self._validate_insights_report_content(input_file)

        base_url = self._get_base_url()

        insights_login = read_insights_login_config()
        auth = (insights_login["username"], insights_login["password"])

        insights_client = InsightsClient(base_url=base_url, auth=auth)
        filename_without_extensions = self._remove_file_extension(input_file)
        with input_file.open("rb") as file_to_be_uploaded:
            files = {
                "file": (
                    filename_without_extensions,
                    file_to_be_uploaded,
                    insights.CONTENT_TYPE,
                )
            }
            successfully_submitted = self._make_publish_request(
                insights_client, insights.INGRESS_REPORT_URI, files
            )
        file_to_be_uploaded.close()

        if not self.args.input_file:
            # remove temporarily downloaded insights report
            input_file.unlink()

        if not successfully_submitted:
            raise SystemExit(1)

    def _handle_response_error(self, response):
        if response.status_code == 404:
            logger.error(_(messages.DOWNLOAD_NO_REPORT_FOUND), self.args.report)
            sys.exit(1)
        return super()._handle_response_error(response)

    def _download_insights_report(self):
        path = (
            insights.REPORT_URI + str(self.args.report) + insights.INSIGHTS_PATH_SUFFIX
        )

        response = qpc_request(
            method=GET,
            path=path,
            headers={"Accept": "application/gzip"},
        )

        if not response.ok:
            self._handle_response_error(response)

        logger.info(_(messages.INSIGHTS_REPORT_DOWNLOAD_SUCCESSFUL))

        output_file = NamedTemporaryFile(suffix=".tar.gz", delete=False)
        output_file_path = Path(output_file.name)
        output_file_path.write_bytes(response.content)

        return output_file_path

    def _get_base_url(self):
        insights_config = read_insights_config()

        if insights_config["use_http"]:
            protocol = "http://"
        else:
            protocol = "https://"
        host = insights_config["host"]
        port = insights_config["port"]

        base_url = f"{protocol}{host}:{port}"
        return base_url

    def _make_publish_request(self, session_client, url, files):
        """Make insights client request and log status code."""
        response = session_client.post(url=url, files=files)
        logger.info(_(messages.INSIGHTS_PUBLISH_RESPONSE), response.text)
        if response.ok:
            logger.info(_(messages.INSIGHTS_PUBLISH_SUCCESSFUL))
            print(response.text)
        elif response.status_code == 401:
            logger.error(_(messages.INSIGHTS_PUBLISH_AUTH_ERROR))
        elif response.status_code == 404:
            logger.error(_(messages.INSIGHTS_PUBLISH_NOT_FOUND_ERROR))
        elif response.status_code == 500:
            logger.error(_(messages.INSIGHTS_PUBLISH_INTERNAL_SERVER_ERROR))

        return response.ok

    def _do_command(self):
        """Execute command flow.

        Sub-commands define this method to perform the required action once
        all options have been verified.
        """
        try:
            self._publish_to_ingress()
        except QPCError as err:
            logger.error(_(err.message))
            SystemExit(1)
