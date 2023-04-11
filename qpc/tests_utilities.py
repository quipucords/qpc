"""Test utilities for the CLI module."""

import contextlib
import sys

DEFAULT_CONFIG = {"host": "127.0.0.1", "port": 8000, "use_http": True}


# pylint: disable=too-few-public-methods
class HushUpStderr:
    """Class used to quiet standard error output."""

    def write(self, stream):
        """Ignore standard error output."""


@contextlib.contextmanager
def redirect_stdout(stream):
    """Run a code block, capturing stdout to the given stream."""
    old_stdout = sys.stdout
    try:
        sys.stdout = stream
        yield
    finally:
        sys.stdout = old_stdout
