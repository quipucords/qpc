"""Utilities for the credential credentials module."""

import sys
import termios
from contextlib import contextmanager
from getpass import getpass
from logging import getLogger
from pathlib import Path

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
    req_payload = _get_attribute_value(
        "password", messages.CONN_PASSWORD, args, req_payload, add_none
    )
    req_payload = _get_ssh_key_value(args, req_payload, add_none)
    req_payload = _get_attribute_value(
        "ssh_passphrase", messages.SSH_PASSPHRASE, args, req_payload, add_none
    )
    req_payload = _get_attribute_value(
        "become_password", messages.BECOME_PASSWORD, args, req_payload, add_none
    )
    req_payload = _get_token_value(args, req_payload, add_none)

    return req_payload


def _get_attribute_value(attribute, prompt, args, req_payload, add_none):
    """Collect the attribute value and place in credential dictionary."""
    if attribute in args and getattr(args, attribute):
        with a_tty():
            print(_(prompt))
            pass_prompt = getpass()
            check_if_prompt_is_not_empty(pass_prompt)
            req_payload[attribute] = pass_prompt
    elif add_none:
        req_payload[attribute] = None

    return req_payload


def _get_ssh_key_value(args, req_payload, add_none):
    """Collect the ssh_key value and place in credential dictionary."""
    if "ssh_keyfile" in args and args.ssh_keyfile:
        try:
            if args.ssh_keyfile == "-":
                if sys.stdin.isatty():
                    print(_(messages.SSH_KEY))
                    pass_prompt = get_multiline_pass(
                        prompt=f"{messages.SSH_KEY_PROMPT}"
                    )
                    check_if_prompt_is_not_empty(pass_prompt)
                else:
                    pass_prompt = "".join(sys.stdin.readlines())
                req_payload["ssh_key"] = pass_prompt
            else:
                try:
                    req_payload["ssh_key"] = Path(args.ssh_keyfile).read_text()
                except FileNotFoundError:
                    logger.error(
                        _(messages.CRED_SSH_KEYFILE_DOES_NOT_EXIST), args.ssh_keyfile
                    )
                    sys.exit(1)
                except PermissionError:
                    logger.error(
                        _(messages.CRED_SSH_KEYFILE_FAILED_TO_READ), args.ssh_keyfile
                    )
                    sys.exit(1)
        except UnicodeDecodeError:
            logger.error(messages.CRED_SSH_KEY_CANNOT_BE_DECODED)
            sys.exit(1)

    elif add_none:
        req_payload["ssh_key"] = None

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
    if "vault_secret_path" in args and args.vault_secret_path:
        req_payload["vault_secret_path"] = args.vault_secret_path
    if "vault_mount_point" in args and args.vault_mount_point:
        req_payload["vault_mount_point"] = args.vault_mount_point

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


def validate_vault_args(args, cred_type=None):
    """Validate vault-related credential arguments.

    :param args: The command line arguments
    :param cred_type: The credential type (for edit command, None for add)
    :returns: None
    :raises SystemExit: If validation fails
    """
    # Get vault options (use getattr for legacy test compatibility)
    vault_secret_path = getattr(args, "vault_secret_path", None)
    vault_mount_point = getattr(args, "vault_mount_point", None)

    if vault_secret_path:
        # Determine credential type from args or parameter
        check_type = cred_type if cred_type else getattr(args, "type", None)

        # Vault options are only valid for openshift and ansible types
        if check_type not in ["openshift", "ansible"]:
            logger.error(_(messages.CRED_VAULT_INVALID_TYPE))
            sys.exit(1)

        # vault_secret_path cannot be used with username/password/sshkeyfile/token
        if (
            getattr(args, "username", None)
            or getattr(args, "password", None)
            or getattr(args, "ssh_keyfile", None)
            or getattr(args, "token", None)
        ):
            logger.error(_(messages.CRED_VAULT_EXCLUSIVE_WITH_CREDS))
            sys.exit(1)

    # vault_mount_point can only be specified if vault_secret_path is specified
    if vault_mount_point and not vault_secret_path:
        logger.error(_(messages.CRED_VAULT_MOUNT_REQUIRES_PATH))
        sys.exit(1)
