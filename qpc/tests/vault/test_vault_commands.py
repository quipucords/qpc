"""Test the vault commands module imports."""

import pytest

from qpc import vault
from qpc.vault.commands import (
    VaultAddCommand,
    VaultClearCommand,
    VaultEditCommand,
    VaultShowCommand,
)


@pytest.mark.usefixtures("server_config")
class TestVaultCommandsImports:
    """Class for testing the vault commands module."""

    def test_commands_imports(self):
        """Test that all command classes can be imported from vault.commands."""
        # Verify all command classes are importable
        assert VaultAddCommand is not None
        assert VaultClearCommand is not None
        assert VaultEditCommand is not None
        assert VaultShowCommand is not None

    def test_commands_classes_have_correct_attributes(self):
        """Test that imported command classes have expected attributes."""
        # Verify class attributes
        assert VaultAddCommand.SUBCOMMAND == vault.SUBCOMMAND
        assert VaultAddCommand.ACTION == vault.ADD
        assert VaultEditCommand.SUBCOMMAND == vault.SUBCOMMAND
        assert VaultEditCommand.ACTION == vault.EDIT
        assert VaultShowCommand.SUBCOMMAND == vault.SUBCOMMAND
        assert VaultShowCommand.ACTION == vault.SHOW
        assert VaultClearCommand.SUBCOMMAND == vault.SUBCOMMAND
        assert VaultClearCommand.ACTION == vault.CLEAR
