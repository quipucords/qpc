"""VaultEditCommand is used to edit HashiCorp Vault configuration."""

import sys
from logging import getLogger

from requests import codes

from qpc import messages, vault
from qpc.clicommand import CliCommand
from qpc.request import PATCH
from qpc.source.utils import validate_port
from qpc.translation import _
from qpc.vault.utils import read_and_encode_cert_file

logger = getLogger(__name__)


class VaultEditCommand(CliCommand):
    """Defines the edit command.

    This command is for editing existing HashiCorp Vault
    configuration for secure credential storage.
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

        self.parser.add_argument(
            "--address",
            dest="address",
            metavar="ADDRESS",
            help=_(messages.VAULT_ADDRESS_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--port",
            dest="port",
            metavar="PORT",
            type=validate_port,
            help=_(messages.VAULT_PORT_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--ssl-verify",
            dest="ssl_verify",
            choices=vault.BOOLEAN_CHOICES,
            type=str.lower,
            help=_(messages.VAULT_SSL_VERIFY_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--client-cert",
            dest="client_cert",
            metavar="CLIENT_CERT_FILE",
            help=_(messages.VAULT_CLIENT_CERT_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--client-key",
            dest="client_key",
            metavar="CLIENT_KEY_FILE",
            help=_(messages.VAULT_CLIENT_KEY_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--ca-cert",
            dest="ca_cert",
            metavar="CA_CERT_FILE",
            help=_(messages.VAULT_CA_CERT_HELP),
            required=False,
        )

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
            self.req_payload["ssl_verify"] = self.args.ssl_verify == "true"

        # Handle certificate files
        if self.args.client_cert and self.args.client_key:
            client_cert_encoded = read_and_encode_cert_file(
                self.args.client_cert, "client certificate"
            )
            client_key_encoded = read_and_encode_cert_file(
                self.args.client_key, "client key"
            )
            self.req_payload["client_cert"] = client_cert_encoded
            self.req_payload["client_key"] = client_key_encoded

        if self.args.ca_cert:
            ca_cert_encoded = read_and_encode_cert_file(
                self.args.ca_cert, "CA certificate"
            )
            self.req_payload["ca_cert"] = ca_cert_encoded

    def _handle_response_success(self):
        logger.info(_(messages.VAULT_UPDATED))
