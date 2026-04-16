"""VaultAddCommand is used to add the HashiCorp Vault server configuration."""

import sys
from logging import getLogger

from requests import codes

from qpc import messages, vault
from qpc.clicommand import CliCommand
from qpc.request import POST
from qpc.translation import _
from qpc.vault.utils import (
    CERT_TYPE_CA,
    CERT_TYPE_CLIENT_CERT,
    CERT_TYPE_CLIENT_KEY,
    add_vault_arguments,
    read_and_encode_cert_file,
    str_to_bool,
)

logger = getLogger(__name__)


class VaultAddCommand(CliCommand):
    """Defines the add command for the HashiCorp Vault server configuration.

    This command is for adding HashiCorp Vault server configuration
    for secure credential storage. This is done by performing an HTTP POST
    to the HashiCorp Vault server Singleton endpoint.
    """

    SUBCOMMAND = vault.SUBCOMMAND
    ACTION = vault.ADD

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            POST,
            vault.VAULT_URI,
            [codes.created, codes.ok],
        )
        add_vault_arguments(self.parser, required_certs=True)

    def _validate_args(self):
        """Validate arguments."""
        CliCommand._validate_args(self)
        ssl_verify_bool = str_to_bool(self.args.ssl_verify)
        if ssl_verify_bool and not self.args.ca_cert:
            logger.error(_(messages.VAULT_CA_CERT_REQUIRED))
            sys.exit(1)

    def _build_data(self):
        """Build request payload."""
        client_cert_encoded = read_and_encode_cert_file(
            self.args.client_cert, CERT_TYPE_CLIENT_CERT
        )
        client_key_encoded = read_and_encode_cert_file(
            self.args.client_key, CERT_TYPE_CLIENT_KEY
        )

        ssl_verify_bool = str_to_bool(self.args.ssl_verify)

        self.req_payload = {
            "address": self.args.address,
            "port": self.args.port,
            "ssl_verify": ssl_verify_bool,
            "client_cert": client_cert_encoded,
            "client_key": client_key_encoded,
        }

        # Add CA cert if provided (required when ssl_verify is True)
        if self.args.ca_cert:
            ca_cert_encoded = read_and_encode_cert_file(self.args.ca_cert, CERT_TYPE_CA)
            self.req_payload["ca_cert"] = ca_cert_encoded

    def _handle_response_success(self):
        logger.info(_(messages.VAULT_CONFIG_SUCCESS))
