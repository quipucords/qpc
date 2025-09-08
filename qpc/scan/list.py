"""ScanListCommand is used to list system scans."""

import urllib.parse as urlparse
from logging import getLogger

from requests import codes

from qpc import messages, scan
from qpc.clicommand import CliCommand
from qpc.request import GET
from qpc.translation import _
from qpc.utils import pretty_format

logger = getLogger(__name__)


def actually_pretty_format(json_data: list[dict]) -> str:
    """
    Format json_data (list of Scan responses) to an even prettier format.

    This outputs an ASCII art like table containing only specific fields,
    and it pads columns dynamically to fit variable width fields in json_data.

    Example output:

       scan_id | scan_name                                | report_id | status
      ---------+------------------------------------------+-----------+-----------
       5       | 1753469322-shrocp4upi417ovn              | 3         | completed
       6       | 1753469427-shrocp4upi417ovn (django-5.2) | 4         | completed
       10      | asdasd                                   | None      | failed
       9       | aws-20250829-a                           | 7         | completed
       8       | dev01-2025-08-28-1328                    | 6         | completed
       7       | net-20250825150855                       | 5         | completed
       1       | scan-1                                   | 1         | completed
       2       | scan-2                                   | 2         | completed

    This function is purpose-made for formatting lists of Scan responses and
    is not suitable for formatting other API responses in its current form.
    """
    minimal_data = []
    for item in json_data:
        relevant = dict()
        relevant["scan_id"] = str(item["id"])
        relevant["scan_name"] = str(item["name"])
        relevant["report_id"] = str(item.get("most_recent", {}).get("report_id", None))
        relevant["status"] = str(item.get("most_recent", {}).get("status", None))
        minimal_data.append(relevant)

    if not minimal_data:
        return _("No scans found.")

    column_widths = {}
    for key in minimal_data[0].keys():
        column_widths[key] = len(key)
    for item in minimal_data:
        for key, value in item.items():
            column_widths[key] = max(column_widths[key], len(str(value)))

    output = (
        "|".join((f" {key.ljust(value)} " for key, value in column_widths.items()))
        + "\n"
    )
    output += (
        "+".join(("-" * (value + 2) for key, value in column_widths.items())) + "\n"
    )
    for item in minimal_data:
        output += (
            "|".join(
                (f" {item[key].ljust(value)} " for key, value in column_widths.items())
            )
            + "\n"
        )
    return output


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
            "--summary",
            dest="output_summary",
            action="store_true",
            help=_("Output results in simplified summary table"),  # TODO FIXME
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
        elif getattr(self.args, "output_summary", False):
            data = actually_pretty_format(results)
            print(data)
        else:
            data = pretty_format(results)
            print(data)

        if json_data.get("next"):
            next_link = json_data.get("next")
            params = urlparse.parse_qs(urlparse.urlparse(next_link).query)
            page = params.get("page", ["1"])[0]
            if self.req_params:
                self.req_params["page"] = page
            else:
                self.req_params = {"page": page}
            self._do_command()
