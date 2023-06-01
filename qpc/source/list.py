"""SourceListCommand is used to list sources for system scans."""

import urllib.parse as urlparse
from logging import getLogger

from requests import codes

from qpc import messages, source
from qpc.clicommand import CliCommand
from qpc.request import GET
from qpc.translation import _
from qpc.utils import pretty_print

logger = getLogger(__name__)


class SourceListCommand(CliCommand):
    """Defines the list command.

    This command is for listing sources which can be later be used with a scan
    to gather facts.
    """

    SUBCOMMAND = source.SUBCOMMAND
    ACTION = source.LIST

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            GET,
            source.SOURCE_URI,
            [codes.ok],
        )
        self.parser.add_argument(
            "--type",
            dest="type",
            choices=source.SOURCE_TYPE_CHOICES,
            metavar="TYPE",
            type=str.lower,
            help=_(messages.SOURCE_TYPE_FILTER_HELP),
            required=False,
        )

    def _build_req_params(self):
        """Add filter by source_type query param."""
        if "type" in self.args and self.args.type:
            self.req_params = {"source_type": self.args.type}

    def _handle_response_success(self):
        json_data = self.response.json()
        count = json_data.get("count", 0)
        results = json_data.get("results", [])
        if count == 0:
            logger.error(_(messages.SOURCE_LIST_NO_SOURCES))
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
            input(_(messages.NEXT_RESULTS))
            self._do_command()
