"""VaultSetCommand is used to set HashiCorp Vault integration."""

import sys
from logging import getLogger

from requests import codes

import qpc.vault as vault
from qpc import messages
from qpc.clicommand import CliCommand
from qpc.request import POST
from qpc.source.utils import validate_port
from qpc.translation import _
from qpc.vault.utils import read_and_encode_cert_file

logger = getLogger(__name__)


class VaultSetCommand(CliCommand):
    """Defines the set command.

    This command is for setting HashiCorp Vault integration
    for secure credential storage.
    """

    SUBCOMMAND = vault.SUBCOMMAND
    ACTION = vault.SET

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

        self.parser.add_argument(
            "--address",
            dest="address",
            metavar="ADDRESS",
            help=_(messages.VAULT_ADDRESS_HELP),
            required=True,
        )
        self.parser.add_argument(
            "--port",
            dest="port",
            metavar="PORT",
            type=validate_port,
            default=8200,
            help=_(messages.VAULT_PORT_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--ssl-verify",
            dest="ssl_verify",
            choices=vault.BOOLEAN_CHOICES,
            type=str.lower,
            default="true",
            help=_(messages.VAULT_SSL_VERIFY_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--client-cert",
            dest="client_cert",
            metavar="CLIENT_CERT_FILE",
            help=_(messages.VAULT_CLIENT_CERT_HELP),
            required=True,
        )
        self.parser.add_argument(
            "--client-key",
            dest="client_key",
            metavar="CLIENT_KEY_FILE",
            help=_(messages.VAULT_CLIENT_KEY_HELP),
            required=True,
        )
        self.parser.add_argument(
            "--ca-cert",
            dest="ca_cert",
            metavar="CA_CERT_FILE",
            help=_(messages.VAULT_CA_CERT_HELP),
            required=False,
        )

    def _validate_args(self):
        """Validate arguments."""
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
        logger.info(_(messages.VAULT_CONFIG_SUCCESS))
