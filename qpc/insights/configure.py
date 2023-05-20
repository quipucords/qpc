"""InsightsConfigureCommand is used to set target host and port for insights publish."""
from logging import getLogger

from qpc import insights, messages
from qpc.clicommand import CliCommand
from qpc.insights.utils import validate_host
from qpc.source.utils import validate_port
from qpc.translation import _
from qpc.utils import (
    DEFAULT_HOST_INSIGHTS_CONFIG,
    DEFAULT_PORT_INSIGHTS_CONFIG,
    write_insights_config,
)

logger = getLogger(__name__)


class InsightsConfigureCommand(CliCommand):
    """Defines insights configure command.

    This command is for configuring the target
    host and port server for insights publish.
    """

    SUBCOMMAND = insights.SUBCOMMAND
    ACTION = insights.CONFIG

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
            default=DEFAULT_HOST_INSIGHTS_CONFIG,
            type=validate_host,
            help=_(messages.INSIGHTS_CONFIG_HOST_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--port",
            dest="port",
            metavar="PORT",
            type=validate_port,
            default=DEFAULT_PORT_INSIGHTS_CONFIG,
            help=_(messages.INSIGHTS_CONFIG_PORT_HELP),
            required=False,
        )
        self.parser.add_argument(
            "--use-http", dest="use_http", action="store_true", required=False
        )

    def _do_command(self):
        """Persist insights configuration."""
        insights_config = {
            "host": self.args.host,
            "port": int(self.args.port),
            "use_http": self.args.use_http,
        }
        write_insights_config(insights_config)
        logger.info(_(messages.INSIGHTS_CONFIG_SUCCESS), insights_config)
