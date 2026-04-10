"""VaultClearCommand is used to clear HashiCorp Vault configuration."""

from logging import getLogger

from requests import codes

from qpc import messages, vault
from qpc.clicommand import CliCommand
from qpc.request import DELETE
from qpc.translation import _

logger = getLogger(__name__)


class VaultClearCommand(CliCommand):
    """Defines the clear command for the HashiCorp Vault configuration.

    This command is for clearing the HashiCorp Vault configuration. This is
    done by deleting the HashiCorp Vault settings Singleton from the server.
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
