"""Module for QPC Exceptions."""


class QPCError(Exception):
    """QPC base error."""

    def __init__(self, message, *args):
        """Take message as mandatory attribute."""
        super().__init__(message, *args)
        self.message = message
