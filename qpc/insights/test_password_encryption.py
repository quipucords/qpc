"""test password encryption."""

import json
import os
import secrets
from pathlib import Path

import pytest

from qpc import utils
from qpc.insights.exceptions import QPCEncryptionKeyError
from qpc.utils import (
    decrypt_password,
    encrypt_password,
    load_encryption_key,
    read_insights_login_config,
    write_encryption_key_if_non_existent,
    write_insights_login_config,
)


@pytest.fixture
def insights_login_file():
    """Path to insights login config file."""
    return Path(utils.INSIGHTS_LOGIN_CONFIG)


def test_password_encryption(insights_login_file: Path):
    """Ensure passwords are encrypted and can be decrypted."""
    write_insights_login_config({"username": "jane_doe", "password": "shadowgirl"})
    loaded_data = json.load(insights_login_file.open())
    assert loaded_data["username"] == "jane_doe"
    assert loaded_data["password"] != "shadowgirl"
    # read login file with the appropriate function
    login_data = read_insights_login_config()
    assert login_data["username"] == "jane_doe"
    assert login_data["password"] == "shadowgirl"


def test_password_encryption_with_key_modified(insights_login_file: Path):
    """Ensure passwords are encrypted and can be decrypted."""
    write_insights_login_config({"username": "jane_doe", "password": "shadowgirl"})
    # recreate encryption key
    Path(utils.INSIGHTS_ENCRYPTION).unlink()
    write_encryption_key_if_non_existent()
    with pytest.raises(QPCEncryptionKeyError):
        read_insights_login_config()


def test_insights_encryption_file_is_created():
    """Test if insights encryption file is created if non-existent."""
    assert not os.path.exists(utils.INSIGHTS_ENCRYPTION)

    write_encryption_key_if_non_existent()

    assert os.path.exists(utils.INSIGHTS_ENCRYPTION)


def test_if_encryption_file_permission_is_set_to_600():
    """Assert encryption file permissions are set to 600 when created."""
    write_encryption_key_if_non_existent()
    stats = os.stat(utils.INSIGHTS_ENCRYPTION)
    print(stats.st_mode)

    assert "600" in oct(stats.st_mode)


def test_if_key_is_loaded_with_wrong_permissions():
    """Assert key is only loaded with right permissions."""
    write_encryption_key_if_non_existent()
    os.chmod(utils.INSIGHTS_ENCRYPTION, 0o777)

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
