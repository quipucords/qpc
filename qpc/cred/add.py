"""CredAddCommand is used to add authentication credentials."""

import sys
from logging import getLogger

from requests import codes

import qpc.cred as credential
from qpc import messages
from qpc.clicommand import CliCommand
from qpc.cred.utils import build_credential_payload
from qpc.request import POST
from qpc.source import SOURCE_TYPE_CHOICES
from qpc.translation import _

logger = getLogger(__name__)


class CredAddCommand(CliCommand):
    """Defines the add command.

    This command is for creating new credentials which
    can be later associated with sources to gather facts.
    """

    SUBCOMMAND = credential.SUBCOMMAND
    ACTION = credential.ADD

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            POST,
            credential.CREDENTIAL_URI,
            [codes.created],
        )

        self.parser.add_argument(
            "--name",
            dest="name",
            metavar="NAME",
            help=_(messages.CRED_NAME_HELP),
            required=True,
        )
        self.parser.add_argument(
            "--type",
            dest="type",
            choices=SOURCE_TYPE_CHOICES,
            metavar="TYPE",
            help=_(messages.CRED_TYPE_HELP),
            type=str.lower,
            required=True,
        )
        self.parser.add_argument(
            "--username",
            dest="username",
            metavar="USERNAME",
            help=_(messages.CRED_USER_HELP),
            required=False,
        )
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--password",
            dest="password",
            action="store_true",
            help=_(messages.CRED_PWD_HELP),
        )
        group.add_argument(
            "--sshkeyfile",
            dest="ssh_keyfile",
            metavar="SSH_KEYFILE",
            help=_(messages.CRED_SSH_KEYFILE_HELP),
        )
        group.add_argument(
            "--token",
            dest="token",
            action="store_true",
            help=_(messages.CRED_TOKEN_HELP),
        )
        group.add_argument(
            "--vault-secret-path",
            dest="vault_secret_path",
            metavar="VAULT_SECRET_PATH",
            help=_(messages.CRED_VAULT_SECRET_PATH_HELP),
        )
        self.parser.add_argument(
            "--vault-mount-point",
            dest="vault_mount_point",
            metavar="VAULT_MOUNT_POINT",
            help=_(messages.CRED_VAULT_MOUNT_POINT_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--sshpassphrase",
            dest="ssh_passphrase",
            action="store_true",
            help=_(messages.CRED_SSH_PASSPHRASE_HELP),
        )
        self.parser.add_argument(
            "--become-method",
            dest="become_method",
            choices=credential.BECOME_CHOICES,
            metavar="BECOME_METHOD",
            help=_(messages.CRED_BECOME_METHOD_HELP),
        )
        self.parser.add_argument(
            "--become-user",
            dest="become_user",
            metavar="BECOME_USER",
            help=_(messages.CRED_BECOME_USER_HELP),
        )
        self.parser.add_argument(
            "--become-password",
            dest="become_password",
            action="store_true",
            help=_(messages.CRED_BECOME_PASSWORD_HELP),
        )

    def _validate_args(self):
        """Validate command arguments."""
        CliCommand._validate_args(self)

        # Get vault options (use getattr for legacy test compatibility)
        vault_secret_path = getattr(self.args, "vault_secret_path", None)
        vault_mount_point = getattr(self.args, "vault_mount_point", None)

        # Validate vault options are only used with openshift or ansible types
        if vault_secret_path:
            if self.args.type not in ["openshift", "ansible"]:
                logger.error(_(messages.CRED_VAULT_INVALID_TYPE))
                sys.exit(1)

            # vault_secret_path cannot be used with username
            if self.args.username:
                logger.error(_(messages.CRED_VAULT_EXCLUSIVE_WITH_CREDS))
                sys.exit(1)

        # vault_mount_point can only be specified if vault_secret_path is specified
        if vault_mount_point and not vault_secret_path:
            logger.error(_(messages.CRED_VAULT_MOUNT_REQUIRES_PATH))
            sys.exit(1)

    def _build_data(self):
        """Construct the dictionary credential given our arguments.

        :returns: a dictionary representing the credential being added
        """
        self.req_payload = build_credential_payload(self.args, self.args.type)

    def _handle_response_success(self):
        logger.info(_(messages.CRED_ADDED), self.args.name)
