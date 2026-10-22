"""Errors for lightspeed module."""

from qpc.exceptions import QPCError


class LightspeedAuthError(QPCError):
    """Class for Lightspeed device authorization errors."""


class QPCLoginConfigError(QPCError):
    """Class for errors in the login config file manipulation."""


class QPCEncryptionKeyError(QPCError):
    """Class for password encryption errors."""
