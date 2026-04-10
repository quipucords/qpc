"""Test the vault commands module imports."""

import pytest

from qpc import vault
from qpc.vault.commands import (
    VaultClearCommand,
    VaultEditCommand,
    VaultSetCommand,
    VaultShowCommand,
    VaultUpdateCommand,
)


@pytest.mark.usefixtures("server_config")
class TestVaultCommandsImports:
    """Class for testing the vault commands module."""

    def test_commands_imports(self):
        """Test that all command classes can be imported from vault.commands."""
        # Verify all command classes are importable
        assert VaultClearCommand is not None
        assert VaultEditCommand is not None
        assert VaultSetCommand is not None
        assert VaultShowCommand is not None
        assert VaultUpdateCommand is not None

    def test_commands_classes_have_correct_attributes(self):
        """Test that imported command classes have expected attributes."""
        # Verify class attributes
        assert VaultSetCommand.SUBCOMMAND == vault.SUBCOMMAND
        assert VaultSetCommand.ACTION == vault.SET
        assert VaultEditCommand.SUBCOMMAND == vault.SUBCOMMAND
        assert VaultEditCommand.ACTION == vault.EDIT
        assert VaultUpdateCommand.SUBCOMMAND == vault.SUBCOMMAND
        assert VaultUpdateCommand.ACTION == vault.UPDATE
        assert VaultShowCommand.SUBCOMMAND == vault.SUBCOMMAND
        assert VaultShowCommand.ACTION == vault.SHOW
        assert VaultClearCommand.SUBCOMMAND == vault.SUBCOMMAND
        assert VaultClearCommand.ACTION == vault.CLEAR
