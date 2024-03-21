"""ScanClearCommand is used to clear one or all host scans."""

import sys
from logging import getLogger

from requests import codes

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import DELETE, GET, POST, request
from qpc.translation import _
from qpc.utils import handle_error_response

logger = getLogger(__name__)


class ScanClearCommand(CliCommand):
    """Defines the clear command.

    This command is for clearing a specific scan or all scans.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.CLEAR

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            GET,
            scan.SCAN_URI,
            [codes.ok],
        )
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--name", dest="name", metavar="NAME", help=_(messages.SCAN_NAME_HELP)
        )
        group.add_argument(
            "--all",
            dest="all",
            action="store_true",
            help=_(messages.SCAN_CLEAR_ALL_HELP),
        )

    def _build_req_params(self):
        if self.args.name:
            self.req_params = {"name": self.args.name}

    def _delete_entry(self, scan_entry, print_out=True):
        deleted = False
        delete_uri = scan.SCAN_URI + str(scan_entry["id"]) + "/"
        response = request(DELETE, delete_uri, parser=self.parser)
        name = scan_entry["name"]
        if response.status_code == codes.no_content:
            deleted = True
            if print_out:
                logger.info(_(messages.SCAN_REMOVED), name)
        else:
            handle_error_response(response)
            if print_out:
                logger.error(_(messages.SCAN_FAILED_TO_REMOVE), name)
        return deleted

    def _delete_all(self) -> bool:
        """Delete all sources."""
        delete_uri = scan.SCAN_BULK_DELETE_URI
        response = request(POST, delete_uri, payload={"ids": "all"}, parser=self.parser)
        # Note: `request` handles most HTTP errors.
        # So, we can trust response.status_code == codes.ok at this point.

        response_json = response.json()
        deleted = response_json.get("deleted", [])
        logger.info(messages.SCAN_CLEAR_ALL_SUMMARY, {"deleted_count": len(deleted)})

    def _handle_response_success(self):  # noqa: C901 PLR0912
        json_data = self.response.json()
        count = json_data.get("count", 0)
        results = json_data.get("results", [])
        if self.args.name and count == 0:
            logger.error(_(messages.SCAN_NOT_FOUND), self.args.name)
            sys.exit(1)
        elif self.args.name and count == 1:
            # delete single scan
            entry = results[0]
            if self._delete_entry(entry) is False:
                sys.exit(1)
        elif self.args.name and count > 1:
            for result in results:
                if result["name"] == self.args.name:
                    if self._delete_entry(result) is False:
                        sys.exit(1)
        elif count == 0:
            logger.error(_(messages.SCAN_NO_SCANS_TO_REMOVE))
            sys.exit(1)
        else:
            self._delete_all()
