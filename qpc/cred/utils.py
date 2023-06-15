"""Utilities for the credential credentials module."""

import sys
import termios
from contextlib import contextmanager
from getpass import getpass
from logging import getLogger

from qpc import messages
from qpc.translation import _
from qpc.utils import check_if_prompt_is_not_empty

logger = getLogger(__name__)


@contextmanager
def a_tty():
    """Make sure that the yielding block is run with a tty."""
    if sys.stdin.isatty():
        yield
    else:
        logger.error(_(messages.PASSWORD_PROMPT_WITH_NO_TTY))
        sys.exit(1)


def get_password(args, req_payload, add_none=True):
    """Collect the credential attribute values and place in credential dictionary.

    :param args: the command line arguments
    :param req_payload: the dictionary for the request
    :param add_none: add None for a key if True vs. not in dictionary
    :returns: the updated dictionary
    """
    req_payload = _get_password_value(args, req_payload, add_none)
    req_payload = _get_ssh_key_value(args, req_payload, add_none)
    req_payload = _get_ssh_passphrase_value(args, req_payload, add_none)
    req_payload = _get_become_password_value(args, req_payload, add_none)
    req_payload = _get_token_value(args, req_payload, add_none)

    return req_payload


def _get_password_value(args, req_payload, add_none):
    """Collect the password value and place in credential dictionary."""
    if "password" in args and args.password:
        with a_tty():
            print(_(messages.CONN_PASSWORD))
            pass_prompt = getpass()
            check_if_prompt_is_not_empty(pass_prompt)
            req_payload["password"] = pass_prompt
    elif add_none:
        req_payload["password"] = None

    return req_payload


def _get_ssh_key_value(args, req_payload, add_none):
    """Collect the ssh_key value and place in credential dictionary."""
    if "ssh_key" in args and args.ssh_key:
        if sys.stdin.isatty():
            print(_(messages.SSH_KEY))
            pass_prompt = get_multiline_pass(prompt=f"{messages.SSH_KEY_PROMPT}")
            check_if_prompt_is_not_empty(pass_prompt)
        else:
            pass_prompt = "".join(sys.stdin.readlines())
        req_payload["ssh_key"] = pass_prompt
    elif add_none:
        req_payload["ssh_key"] = None

    return req_payload


def _get_ssh_passphrase_value(args, req_payload, add_none):
    """Collect the ssh_passphrase value and place in credential dictionary."""
    if "ssh_passphrase" in args and args.ssh_passphrase:
        with a_tty():
            print(_(messages.SSH_PASSPHRASE))
            pass_prompt = getpass()
            check_if_prompt_is_not_empty(pass_prompt)
            req_payload["ssh_passphrase"] = pass_prompt
    elif add_none:
        req_payload["ssh_passphrase"] = None

    return req_payload


def _get_become_password_value(args, req_payload, add_none):
    """Collect the become_password value and place in credential dictionary."""
    if "become_password" in args and args.become_password:
        with a_tty():
            print(_(messages.BECOME_PASSWORD))
            pass_prompt = getpass()
            check_if_prompt_is_not_empty(pass_prompt)
            req_payload["become_password"] = pass_prompt
    elif add_none:
        req_payload["become_password"] = None

    return req_payload


def _get_token_value(args, req_payload, add_none):
    """Collect the token value and place in credential dictionary."""
    if getattr(args, "token", None):
        with a_tty():
            token_prompt = getpass(messages.AUTH_TOKEN)
            check_if_prompt_is_not_empty(token_prompt)
            req_payload["auth_token"] = token_prompt
    elif add_none:
        req_payload["auth_token"] = None

    return req_payload


def build_credential_payload(args, cred_type, add_none=True):
    """Construct payload from command line arguments.

    :param args: the command line arguments
    :param add_none: add None for a key if True vs. not in dictionary
    :returns: the dictionary for the request payload
    """
    req_payload = {"name": args.name}
    if "type" in args and cred_type is not None:
        req_payload["cred_type"] = cred_type
    if "username" in args and args.username:
        req_payload["username"] = args.username
    if "become_method" in args and args.become_method:
        req_payload["become_method"] = args.become_method
    if "become_user" in args and args.become_user:
        req_payload["become_user"] = args.become_user
    if "filename" in args and args.filename:
        req_payload["ssh_keyfile"] = args.filename
    elif add_none:
        req_payload["ssh_keyfile"] = None

    req_payload = get_password(args, req_payload, add_none)
    return req_payload


def get_multiline_pass(prompt="Password: "):
    """Multiline no-echo password input using Posix tty controls."""
    sys.stderr.write(prompt)
    sys.stderr.flush()

    local_mode_flags_position = (
        3  # By POSIX/C Convention, the 'lflag' bit-wise flags are in slot `[3]`
    )
    stdin_fd = sys.stdin.fileno()
    original_tty_attributes = termios.tcgetattr(stdin_fd)
    tty_attributes_without_echo = list(original_tty_attributes)
    tty_attributes_without_echo[local_mode_flags_position] &= ~termios.ECHO

    multiline_password = []
    try:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, tty_attributes_without_echo)
        multiline_password = sys.stdin.readlines()
    finally:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, original_tty_attributes)
        sys.stderr.flush()
    sys.stderr.write("\n")
    return "".join(multiline_password)
