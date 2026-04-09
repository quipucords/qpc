"""VaultUpdateCommand is used to update HashiCorp Vault integration."""

import sys
from logging import getLogger

from requests import codes

from qpc import messages, vault
from qpc.clicommand import CliCommand
from qpc.request import PUT
from qpc.translation import _
from qpc.vault.utils import add_vault_arguments, read_and_encode_cert_file

logger = getLogger(__name__)


class VaultUpdateCommand(CliCommand):
    """Defines the update command.

    This command is for updating HashiCorp Vault integration
    for secure credential storage.
    """

    SUBCOMMAND = vault.SUBCOMMAND
    ACTION = vault.UPDATE

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            PUT,
            vault.VAULT_URI,
            [codes.ok],
        )

        add_vault_arguments(self.parser, required_certs=True)

    def _validate_args(self):
        """Validate arguments."""
        CliCommand._validate_args(self)
        # Convert string "true"/"false" to boolean for validation
        ssl_verify_bool = self.args.ssl_verify == "true"
        if ssl_verify_bool and not self.args.ca_cert:
            logger.error(_(messages.VAULT_CA_CERT_REQUIRED))
            sys.exit(1)

    def _build_data(self):
        """Build request payload."""
        # Read and encode certificate files
        client_cert_encoded = read_and_encode_cert_file(
            self.args.client_cert, "client certificate"
        )
        client_key_encoded = read_and_encode_cert_file(
            self.args.client_key, "client key"
        )

        # Convert string "true"/"false" to boolean
        ssl_verify_bool = self.args.ssl_verify == "true"

        self.req_payload = {
            "address": self.args.address,
            "port": self.args.port,
            "ssl_verify": ssl_verify_bool,
            "client_cert": client_cert_encoded,
            "client_key": client_key_encoded,
        }

        # Add CA cert if provided (required when ssl_verify is True)
        if self.args.ca_cert:
            ca_cert_encoded = read_and_encode_cert_file(
                self.args.ca_cert, "CA certificate"
            )
            self.req_payload["ca_cert"] = ca_cert_encoded

    def _handle_response_success(self):
        logger.info(_(messages.VAULT_UPDATED))
