#!/usr/bin/env python
#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""InsightsAddLoginCommand is used to save insights login configuration."""

from logging import getLogger

from qpc import insights, messages
from qpc.clicommand import CliCommand
from qpc.exceptions import QPCError
from qpc.insights.utils import validate_username_and_password
from qpc.translation import _
from qpc.utils import write_insights_login_config

log = getLogger("qpc")


class InsightsAddLoginCommand(CliCommand):
    """Define insights add_login command.

    This command is for storing insights
    login information, username and password
    """

    SUBCOMMAND = insights.SUBCOMMAND
    ACTION = insights.ADD_LOGIN

    def __init__(self, subparsers):
        """Create command."""
        super().__init__(
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            None,
            None,
            [],
        )
        self.parser.add_argument(
            "--username",
            dest="username",
            metavar="USERNAME",
            type=validate_username_and_password,
            help=_(messages.INSIGHTS_ADD_USERNAME_USER_HELP),
            required=True,
        )
        self.parser.add_argument(
            "--password",
            dest="password",
            type=validate_username_and_password,
            metavar="PASSWORD",
            help=_(messages.INSIGHTS_ADD_PASS_USER_HELP),
            required=True,
        )

    def _do_command(self):
        """Persist insights login configuration."""
        login_config = {
            "username": self.args.username,
            "password": self.args.password,
        }
        try:
            write_insights_login_config(login_config)
        except QPCError as err:
            log.error(_(err.message))
            SystemExit(1)
        log.info(_(messages.INSIGHTS_LOGIN_CONFIG_SUCCESS))
