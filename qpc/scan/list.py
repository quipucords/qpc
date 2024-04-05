"""ScanListCommand is used to list system scans."""

import time
import urllib.parse as urlparse
from logging import getLogger

from requests import codes

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import GET
from qpc.translation import _
from qpc.utils import pretty_print

logger = getLogger(__name__)


class ScanListCommand(CliCommand):
    """Defines the list command.

    This command is for listing sources scans used to gather system facts.
    """

    SUBCOMMAND = scan.SUBCOMMAND
    ACTION = scan.LIST

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
        self.parser.add_argument(
            "--type",
            dest="type",
            choices=[scan.SCAN_TYPE_CONNECT, scan.SCAN_TYPE_INSPECT],
            metavar="TYPE",
            help=_(messages.SCAN_TYPE_FILTER_HELP),
            required=False,
        )
        self.req_params = {}

    def _build_req_params(self):
        """Add filter by scan_type/state query param."""
        if "type" in self.args and self.args.type:
            self.req_params["scan_type"] = self.args.type

    def _handle_response_success(self):
        json_data = self.response.json()
        count = json_data.get("count", 0)
        results = json_data.get("results", [])
        if count == 0:
            logger.error(_(messages.SCAN_LIST_NO_SCANS))
        else:
            data = pretty_print(results)
            print(data)

        if json_data.get("next"):
            next_link = json_data.get("next")
            params = urlparse.parse_qs(urlparse.urlparse(next_link).query)
            page = params.get("page", ["1"])[0]
            if self.req_params:
                self.req_params["page"] = page
            else:
                self.req_params = {"page": page}
            time.sleep(1)
            self._do_command()
