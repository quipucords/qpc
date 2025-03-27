"""ConfigureHostCommand is used to set target host and port server."""

from argparse import SUPPRESS
from logging import getLogger

import qpc.server as config
from qpc import messages
from qpc.clicommand import CliCommand
from qpc.source.utils import validate_port
from qpc.translation import _
from qpc.utils import (
    CONFIG_HOST_KEY,
    CONFIG_PORT_KEY,
    CONFIG_SSL_VERIFY,
    CONFIG_USE_HTTP,
    write_server_config,
)

logger = getLogger(__name__)


class ConfigureHostCommand(CliCommand):
    """Defines the configure host command.

    This command is for configuring the target
    host and port server for the CLI.
    """

    SUBCOMMAND = config.SUBCOMMAND
    ACTION = config.CONFIG

    def __init__(self, subparsers):
        """Create command."""
        CliCommand.__init__(
            self,
            self.SUBCOMMAND,
            self.ACTION,
            subparsers.add_parser(self.ACTION),
            None,
            None,
            [],
        )
        self.parser.add_argument(
            "--host",
            dest="host",
            metavar="HOST",
            help=_(messages.SERVER_CONFIG_HOST_HELP),
            required=True,
        )
        self.parser.add_argument(
            "--port",
            dest="port",
            metavar="PORT",
            type=validate_port,
            default=9443,
            help=_(messages.SERVER_CONFIG_PORT_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--ssl-verify",
            dest="ssl_verify",
            metavar="CERT_PATH",
            help=_(messages.SERVER_CONFIG_SSL_CERT_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--use-http",
            dest="use_http",
            action="store_true",
            help=SUPPRESS,
            required=False,
        )

    def _do_command(self):
        """Persist the server configuration."""
        server_config = {
            CONFIG_HOST_KEY: self.args.host,
            CONFIG_PORT_KEY: int(self.args.port),
            CONFIG_USE_HTTP: self.args.use_http,
            CONFIG_SSL_VERIFY: self.args.ssl_verify,
        }
        write_server_config(server_config)
        protocol = "https"
        if self.args.use_http:
            protocol = "http"
        logger.info(
            _(messages.SERVER_CONFIG_SUCCESS),
            {
                "protocol": protocol,
                "host": self.args.host,
                "port": self.args.port,
            },
        )
