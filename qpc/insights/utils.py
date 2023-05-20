"""Utilities for the insights module."""


import re
from argparse import ArgumentTypeError
from getpass import getpass

from qpc import messages
from qpc.utils import check_if_prompt_is_not_empty


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


def validate_username_and_password(arg):
    """Validate password and username syntax.

    :param arg: a string
    :returns: The validated argument
    :raises: ArgumentTypeError, if argument is invalid
    """
    argument_re = re.compile(r"^\S+$")
    if argument_re.search(arg) is None:
        raise ArgumentTypeError("The argument value is invalid.")
    return arg


def build_insights_login_config_dict(args):
    """Construct login config dict from command line arguments.

    :param args: the command line arguments
    :returns: insights login config dict
    """
    config_dict = {}
    config_dict["username"] = args.username
    if getattr(args, "password", None):
        password_prompt = getpass(messages.INSIGHTS_LOGIN_PASSWORD)
        check_if_prompt_is_not_empty(password_prompt)
        validate_username_and_password(password_prompt)
        config_dict["password"] = password_prompt
    return config_dict
