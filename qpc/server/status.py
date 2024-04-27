"""ServerStatusCommand is used to show the server status."""

import sys
from logging import getLogger

from requests import codes

from qpc import messages, server
from qpc.clicommand import CliCommand
from qpc.request import GET
from qpc.translation import _
from qpc.utils import pretty_format, validate_write_file, write_file

logger = getLogger(__name__)


class ServerStatusCommand(CliCommand):
    """Defines the server status command.

    This command is viewing the server version.
    """

    SUBCOMMAND = server.SUBCOMMAND
    ACTION = server.STATUS

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            GET,
            server.STATUS_URI,
            [codes.ok],
        )
        self.parser.add_argument(
            "--output-file",
            dest="path",
            metavar="PATH",
            help=_(messages.STATUS_PATH_HELP),
            required=False,
        )

    def _validate_args(self):
        CliCommand._validate_args(self)
        if self.args.path:
            try:
                validate_write_file(self.args.path, "output-file")
            except ValueError as error:
                logger.error(error)
                sys.exit(1)

    def _build_req_params(self):
        self.req_path = server.STATUS_URI

    def _handle_response_success(self):
        json_data = self.response.json()
        status = pretty_format(json_data)
        if self.args.path:
            try:
                write_file(self.args.path, status)
                logger.info(_(messages.STATUS_SUCCESSFULLY_WRITTEN))
            except EnvironmentError as err:
                logger.error(
                    _(messages.WRITE_FILE_ERROR), {"path": self.args.path, "error": err}
                )
        else:
            print(status)

    def _handle_response_error(self):
        logger.error(_(messages.SERVER_STATUS_FAILURE))
        sys.exit(1)
