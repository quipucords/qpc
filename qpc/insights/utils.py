"""Utilities for the insights module."""

import re
from argparse import ArgumentTypeError


def validate_host(arg):
    """Validate hostname syntax.

    :param arg: a string
    :returns: the validated argument
    :raises: ArgumentTypeError, if argument is invalid
    """
    host_re = re.compile(
        r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*"
        r"([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
    )
    if host_re.search(arg) is None:
        raise ArgumentTypeError(f"Host value {arg} should be a valid hostname")
    return arg
