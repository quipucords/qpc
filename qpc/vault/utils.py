"""Utilities for the vault module."""

import base64
import sys
from logging import getLogger
from pathlib import Path

from qpc import messages, vault
from qpc.source.utils import validate_port
from qpc.translation import _

logger = getLogger(__name__)

# Certificate type constants for error messages
CERT_TYPE_CA = "CA certificate"
CERT_TYPE_CLIENT_CERT = "Client certificate"
CERT_TYPE_CLIENT_KEY = "Client key"


def read_and_encode_cert_file(file_path, file_type):
    """Read a certificate/key file and return base64 encoded single-line string.

    :param file_path: path to the certificate or key file
    :param file_type: type of file for error messages (e.g., 'client certificate')
    :returns: base64 encoded string
    """
    try:
        file_content = Path(file_path).read_bytes()
        # Base64 encode and convert to UTF-8 string
        return base64.b64encode(file_content).decode("utf-8")
    except FileNotFoundError:
        logger.error(_(messages.VAULT_CERT_FILE_NOT_FOUND), file_type, file_path)
        sys.exit(1)
    except PermissionError:
        logger.error(
            _(messages.VAULT_CERT_FILE_PERMISSION_DENIED), file_type, file_path
        )
        sys.exit(1)
    except (OSError, UnicodeDecodeError) as e:
        logger.error(
            _(messages.VAULT_CERT_FILE_READ_ERROR), file_type, file_path, str(e)
        )
        sys.exit(1)


def str_to_bool(value):
    """Convert string 'true'/'false' to boolean.

    :param value: string value ('true' or 'false')
    :returns: boolean
    """
    return value == "true"


def add_vault_arguments(parser, required_certs=True, required_address=True):
    """Add common vault arguments to argument parser.

    :param parser: ArgumentParser to add arguments to
    :param required_certs: Whether client cert/key are required
    :param required_address: Whether address is required
    """
    parser.add_argument(
        "--address",
        dest="address",
        metavar="ADDRESS",
        help=_(messages.VAULT_ADDRESS_HELP),
        required=required_address,
    )
    parser.add_argument(
        "--port",
        dest="port",
        metavar="PORT",
        type=validate_port,
        default=8200,
        help=_(messages.VAULT_PORT_HELP),
        required=False,
    )
    parser.add_argument(
        "--ssl-verify",
        dest="ssl_verify",
        choices=vault.BOOLEAN_CHOICES,
        type=str.lower,
        default="true" if required_certs else None,
        help=_(messages.VAULT_SSL_VERIFY_HELP),
        required=False,
    )
    parser.add_argument(
        "--client-cert",
        dest="client_cert",
        metavar="CLIENT_CERT_FILE",
        help=_(messages.VAULT_CLIENT_CERT_HELP),
        required=required_certs,
    )
    parser.add_argument(
        "--client-key",
        dest="client_key",
        metavar="CLIENT_KEY_FILE",
        help=_(messages.VAULT_CLIENT_KEY_HELP),
        required=required_certs,
    )
    parser.add_argument(
        "--ca-cert",
        dest="ca_cert",
        metavar="CA_CERT_FILE",
        help=_(messages.VAULT_CA_CERT_HELP),
        required=False,
    )
