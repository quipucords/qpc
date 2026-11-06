"""LightspeedConfigureCommand sets target host and port for Lightspeed publish."""

from logging import getLogger

from qpc import lightspeed, messages
from qpc.clicommand import CliCommand
from qpc.lightspeed.utils import validate_host
from qpc.source.utils import validate_port
from qpc.translation import _
from qpc.utils import (
    CONFIG_HOST_KEY,
    CONFIG_PORT_KEY,
    CONFIG_SSO_HOST_KEY,
    CONFIG_USE_HTTP,
    DEFAULT_HOST_LIGHTSPEED_CONFIG,
    DEFAULT_PORT_LIGHTSPEED_CONFIG,
    DEFAULT_SSO_HOST_LIGHTSPEED_CONFIG,
    write_lightspeed_config,
)

logger = getLogger(__name__)


class LightspeedConfigureCommand(CliCommand):
    """Defines lightspeed configure command.

    This command is for configuring the target
    host and port server for lightspeed publish.
    """

    SUBCOMMAND = lightspeed.SUBCOMMAND
    ACTION = lightspeed.CONFIG

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
            "--host",
            dest="host",
            metavar="HOST",
            default=DEFAULT_HOST_LIGHTSPEED_CONFIG,
            type=validate_host,
            help=_(messages.LIGHTSPEED_CONFIG_HOST_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--port",
            dest="port",
            metavar="PORT",
            type=validate_port,
            default=DEFAULT_PORT_LIGHTSPEED_CONFIG,
            help=_(messages.LIGHTSPEED_CONFIG_PORT_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--use-http", dest="use_http", action="store_true", required=False
        )
        self.parser.add_argument(
            "--sso-host",
            dest="sso_host",
            metavar="SSO_HOST",
            default=DEFAULT_SSO_HOST_LIGHTSPEED_CONFIG,
            type=validate_host,
            help=_(messages.LIGHTSPEED_CONFIG_SSO_HOST_HELP),
            required=False,
        )

    def _do_command(self):
        """Persist lightspeed configuration."""
        lightspeed_config = {
            CONFIG_HOST_KEY: self.args.host,
            CONFIG_PORT_KEY: int(self.args.port),
            CONFIG_USE_HTTP: self.args.use_http,
            CONFIG_SSO_HOST_KEY: self.args.sso_host,
        }
        write_lightspeed_config(lightspeed_config)
        logger.info(_(messages.LIGHTSPEED_CONFIG_SUCCESS), lightspeed_config)
