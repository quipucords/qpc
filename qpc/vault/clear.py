"""VaultClearCommand is used to clear HashiCorp Vault configuration."""

from logging import getLogger

from requests import codes

import qpc.vault as vault
from qpc import messages
from qpc.clicommand import CliCommand
from qpc.request import DELETE
from qpc.translation import _

logger = getLogger(__name__)


class VaultClearCommand(CliCommand):
    """Defines the clear command.

    This command is for clearing the HashiCorp Vault configuration.
    """

    SUBCOMMAND = vault.SUBCOMMAND
    ACTION = vault.CLEAR

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            DELETE,
            vault.VAULT_URI,
            [codes.no_content],
        )

    def _handle_response_success(self):
        logger.info(_(messages.VAULT_CLEARED))
