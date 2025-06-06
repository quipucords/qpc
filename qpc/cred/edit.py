"""CredEditCommand is used to edit credentials."""

import sys
from logging import getLogger

from requests import codes

import qpc.cred as credential
from qpc import messages
from qpc.clicommand import CliCommand
from qpc.cred.utils import build_credential_payload
from qpc.request import GET, PATCH, request
from qpc.translation import _

logger = getLogger(__name__)


class CredEditCommand(CliCommand):
    """Defines the edit command.

    This command is for editing existing credentials
    which can be later associated with sources to gather facts.
    """

    SUBCOMMAND = credential.SUBCOMMAND
    ACTION = credential.EDIT

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            PATCH,
            credential.CREDENTIAL_URI,
            [codes.ok],
        )
        self.parser.add_argument(
            "--name",
            dest="name",
            metavar="NAME",
            help=_(messages.CRED_NAME_HELP),
            required=True,
        )
        self.parser.add_argument(
            "--username",
            dest="username",
            metavar="USERNAME",
            help=_(messages.CRED_USER_HELP),
            required=False,
        )
        group = self.parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
            "--password",
            dest="password",
            action="store_true",
            help=_(messages.CRED_PWD_HELP),
        )
        group.add_argument(
            "--token",
            dest="token",
            action="store_true",
            help=_(messages.CRED_TOKEN_HELP),
        )
        group.add_argument(
            "--sshkeyfile",
            dest="ssh_keyfile",
            metavar="SSH_KEYFILE",
            help=_(messages.CRED_SSH_KEYFILE_HELP),
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
        self.cred_type = None

    def _validate_args(self):
        CliCommand._validate_args(self)

        if not (
            self.args.username
            or self.args.password
            or self.args.ssh_keyfile
            or self.args.ssh_passphrase
            or self.args.become_method
            or self.args.become_user
            or self.args.become_password
            or self.args.token
        ):
            logger.error(_(messages.CRED_EDIT_NO_ARGS), self.args.name)
            self.parser.print_help()
            sys.exit(1)

        # check for existence of credential
        response = request(
            parser=self.parser,
            method=GET,
            path=credential.CREDENTIAL_URI,
            params={"name": self.args.name},
            payload=None,
        )
        if response.status_code == codes.ok:
            json_data = response.json()
            count = json_data.get("count", 0)
            if count == 1:
                cred_entry = json_data.get("results")[0]
                self.cred_type = cred_entry["cred_type"]
                self.req_path = self.req_path + str(cred_entry["id"]) + "/"
            else:
                logger.error(_(messages.CRED_DOES_NOT_EXIST), self.args.name)
                sys.exit(1)
        else:
            logger.error(_(messages.CRED_DOES_NOT_EXIST), self.args.name)
            sys.exit(1)

    def _build_data(self):
        """Construct the dictionary credential given our arguments.

        :returns: a dictionary representing the credential being added
        """
        self.req_payload = build_credential_payload(
            self.args, self.cred_type, add_none=False
        )

    def _handle_response_success(self):
        logger.info(_(messages.CRED_UPDATED), self.args.name)
