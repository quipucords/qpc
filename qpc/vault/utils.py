"""Utilities for the vault module."""

import base64
import sys
from logging import getLogger
from pathlib import Path

from qpc import messages
from qpc.translation import _

logger = getLogger(__name__)


def read_and_encode_cert_file(file_path, file_type):
    """Read a certificate/key file and return base64 encoded single-line string.

    :param file_path: path to the certificate or key file
    :param file_type: type of file for error messages (e.g., 'client certificate')
    :returns: base64 encoded string
    """
    try:
        file_content = Path(file_path).read_bytes()
        # Base64 encode and convert to UTF-8 string
        encoded_content = base64.b64encode(file_content).decode("utf-8")
        return encoded_content
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
