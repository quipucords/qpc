"""Utilities for the credential credentials module."""

from getpass import getpass
from logging import getLogger

from qpc import messages
from qpc.translation import _
from qpc.utils import check_if_prompt_is_not_empty

logger = getLogger(__name__)


def get_password(args, req_payload, add_none=True):
    """Collect the password value and place in credential dictionary.

    :param args: the command line arguments
    :param req_payload: the dictionary for the request
    :param add_none: add None for a key if True vs. not in dictionary
    :returns: the updated dictionary
    """
    if "password" in args and args.password:
        print(_(messages.CONN_PASSWORD))
        pass_prompt = getpass()
        check_if_prompt_is_not_empty(pass_prompt)
        req_payload["password"] = pass_prompt
    elif add_none:
        req_payload["password"] = None
    if "ssh_passphrase" in args and args.ssh_passphrase:
        print(_(messages.SSH_PASSPHRASE))
        pass_prompt = getpass()
        check_if_prompt_is_not_empty(pass_prompt)
        req_payload["ssh_passphrase"] = pass_prompt
    elif add_none:
        req_payload["ssh_passphrase"] = None
    if "become_password" in args and args.become_password:
        print(_(messages.BECOME_PASSWORD))
        pass_prompt = getpass()
        check_if_prompt_is_not_empty(pass_prompt)
        req_payload["become_password"] = pass_prompt
    elif add_none:
        req_payload["become_password"] = None
    if getattr(args, "token", None):
        token_prompt = getpass(messages.OPENSHIFT_TOKEN)
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
