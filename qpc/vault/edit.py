"""VaultEditCommand is used to edit HashiCorp Vault configuration."""

import sys
from logging import getLogger

from requests import codes

from qpc import messages, vault
from qpc.clicommand import CliCommand
from qpc.request import PATCH
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


class VaultEditCommand(CliCommand):
    """Defines the edit command for the HashiCorp Vault server configuration.

    This command is for editing the existing HashiCorp Vault configuration for
    secure credential storage. This is done via an HTTP PATCH request
    to the HachiCorp Vault Singleton allowing us to edit one or more
    Vault server settings.
    """

    SUBCOMMAND = vault.SUBCOMMAND
    ACTION = vault.EDIT

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            PATCH,
            vault.VAULT_URI,
            [codes.ok],
        )

        add_vault_arguments(self.parser, required_certs=False, required_address=False)

    def _validate_args(self):
        CliCommand._validate_args(self)

        # Check if both client_cert and client_key are provided together
        if bool(self.args.client_cert) != bool(self.args.client_key):
            logger.error(_(messages.VAULT_CLIENT_CERT_KEY_MISMATCH))
            sys.exit(1)

        has_data = (
            self.args.address
            or self.args.port
            or self.args.ssl_verify
            or self.args.client_cert
            or self.args.client_key
            or self.args.ca_cert
        )
        if not has_data:
            logger.error(_(messages.VAULT_EDIT_NO_ARGS))
            sys.exit(1)

    def _build_data(self):
        """Build request payload."""
        self.req_payload = {}

        if self.args.address:
            self.req_payload["address"] = self.args.address
        if self.args.port:
            self.req_payload["port"] = self.args.port
        if self.args.ssl_verify is not None:
            # Convert string "true"/"false" to boolean
            self.req_payload["ssl_verify"] = str_to_bool(self.args.ssl_verify)

        # Handle certificate files
        if self.args.client_cert and self.args.client_key:
            client_cert_encoded = read_and_encode_cert_file(
                self.args.client_cert, CERT_TYPE_CLIENT_CERT
            )
            client_key_encoded = read_and_encode_cert_file(
                self.args.client_key, CERT_TYPE_CLIENT_KEY
            )
            self.req_payload["client_cert"] = client_cert_encoded
            self.req_payload["client_key"] = client_key_encoded

        if self.args.ca_cert:
            ca_cert_encoded = read_and_encode_cert_file(self.args.ca_cert, CERT_TYPE_CA)
            self.req_payload["ca_cert"] = ca_cert_encoded

    def _handle_response_success(self):
        logger.info(_(messages.VAULT_UPDATED))
