"""test password encryption."""

import secrets

import pytest

from qpc import utils
from qpc.insights.exceptions import QPCEncryptionKeyError
from qpc.utils import (
    decrypt_password,
    encrypt_password,
    load_encryption_key,
    write_encryption_key_if_non_existent,
)


def test_insights_encryption_file_is_created():
    """Test if insights encryption file is created if non-existent."""
    assert not utils.INSIGHTS_ENCRYPTION.exists()

    write_encryption_key_if_non_existent()

    assert utils.INSIGHTS_ENCRYPTION.exists()


def test_if_encryption_file_permission_is_set_to_600():
    """Assert encryption file permissions are set to 600 when created."""
    write_encryption_key_if_non_existent()
    stats = utils.INSIGHTS_ENCRYPTION.stat()
    print(stats.st_mode)

    assert "600" in oct(stats.st_mode)


def test_if_key_is_loaded_with_wrong_permissions():
    """Assert key is only loaded with right permissions."""
    write_encryption_key_if_non_existent()
    utils.INSIGHTS_ENCRYPTION.chmod(0o777)

    with pytest.raises(QPCEncryptionKeyError):
        load_encryption_key()


def test_if_key_is_loaded_with_appropriate_permissions():
    """Assert key is only loaded with right permissions."""
    write_encryption_key_if_non_existent()
    key = load_encryption_key()

    assert key is not None


@pytest.mark.parametrize(
    "password",
    [
        secrets.token_urlsafe(13),
        secrets.token_urlsafe(8),
        secrets.token_urlsafe(10),
        secrets.token_urlsafe(20),
        secrets.token_urlsafe(5),
    ],
)
def test_passwords_are_encrypted_and_decrypted_successfully(password):
    """Test if several passwords are encrypted and decrypted successfully."""
    encrypted_password = encrypt_password(password)
    decrypted_password = decrypt_password(encrypted_password)

    assert password == decrypted_password
