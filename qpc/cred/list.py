"""CredListCommand is used to list authentication credentials."""

import urllib.parse as urlparse
from logging import getLogger

from requests import codes

import qpc.cred as credential
from qpc import messages
from qpc.clicommand import CliCommand
from qpc.request import GET
from qpc.translation import _
from qpc.utils import pretty_print

logger = getLogger(__name__)


# pylint: disable=too-few-public-methods
class CredListCommand(CliCommand):
    """Defines the list command.

    This command is for listing credentials which can be later associated with
    sources to gather facts.
    """

    SUBCOMMAND = credential.SUBCOMMAND
    ACTION = credential.LIST

    def __init__(self, subparsers):
        """Create command."""
        # pylint: disable=no-member
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            GET,
            credential.CREDENTIAL_URI,
            [codes.ok],
        )
        self.parser.add_argument(
            "--type",
            dest="type",
            choices=[
                credential.NETWORK_CRED_TYPE,
                credential.VCENTER_CRED_TYPE,
                credential.SATELLITE_CRED_TYPE,
                credential.OPENSHIFT_CRED_TYPE,
            ],
            metavar="TYPE",
            type=str.lower,
            help=_(messages.CRED_TYPE_FILTER_HELP),
            required=False,
        )

    def _build_req_params(self):
        """Add filter by cred_type query param."""
        if "type" in self.args and self.args.type:
            self.req_params = {"cred_type": self.args.type}

    def _handle_response_success(self):
        json_data = self.response.json()
        count = json_data.get("count", 0)
        results = json_data.get("results", [])
        if count == 0:
            logger.error(_(messages.CRED_LIST_NO_CREDS))
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
