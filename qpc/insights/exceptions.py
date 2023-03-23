"""Errors for insights module."""


from qpc.exceptions import QPCError


class QPCLoginConfigError(QPCError):
    """Class for errors in the login config file manipulation."""


class QPCEncryptionKeyError(QPCError):
    """Class for password encryption errors."""
