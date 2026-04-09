"""VaultShowCommand is used to show HashiCorp Vault configuration."""

import json
import sys
from logging import getLogger

from requests import codes

from qpc import messages, vault
from qpc.clicommand import CliCommand
from qpc.request import GET
from qpc.translation import _

logger = getLogger(__name__)


class VaultShowCommand(CliCommand):
    """Defines the show command.

    This command is for showing the current HashiCorp Vault
    configuration for secure credential storage.
    """

    SUBCOMMAND = vault.SUBCOMMAND
    ACTION = vault.SHOW

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            GET,
            vault.VAULT_URI,
            [codes.ok],
        )

    def _handle_response_success(self):
        try:
            json_data = self.response.json()
            formatted_json = json.dumps(
                json_data, sort_keys=True, indent=4, separators=(",", ": ")
            )
            print(formatted_json)
        except ValueError:
            logger.error(_(messages.VAULT_INVALID_JSON_RESPONSE))
            sys.exit(1)
