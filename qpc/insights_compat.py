# TODO: remove after 2.10 release when CI no longer uses `insights` subcommand/commands
# To remove: git revert <this-commit-sha> (see DISCOVERY-1571)
"""Deprecated backward-compatible aliases for the insights → lightspeed rename.

All classes in this module are thin wrappers that log a deprecation warning and
delegate to the corresponding ``lightspeed`` command.  They exist only to keep
legacy CI pipelines working while they migrate to the new names.
"""

import warnings
from logging import getLogger
from pathlib import Path
from tempfile import NamedTemporaryFile

from qpc import messages
from qpc.lightspeed import REPORT_URI
from qpc.lightspeed.configure import LightspeedConfigureCommand
from qpc.lightspeed.login import LightspeedLoginCommand
from qpc.lightspeed.publish import LightspeedPublishCommand
from qpc.request import GET
from qpc.request import request as qpc_request
from qpc.translation import _

logger = getLogger(__name__)

_DEPRECATION_MSG = (
    "The `insights` subcommand is deprecated and will be removed after the 2.10 "
    "release. Use `lightspeed` instead."
)

SUBCOMMAND = "insights"


def _warn():
    warnings.warn(_DEPRECATION_MSG, DeprecationWarning, stacklevel=3)
    logger.warning(_DEPRECATION_MSG)


class InsightsConfigureCommand(LightspeedConfigureCommand):
    """Deprecated: use ``lightspeed config`` instead."""

    SUBCOMMAND = SUBCOMMAND

    def _validate_args(self):
        _warn()
        super()._validate_args()


class InsightsLoginCommand(LightspeedLoginCommand):
    """Deprecated: use ``lightspeed login`` instead."""

    SUBCOMMAND = SUBCOMMAND

    def _validate_args(self):
        _warn()
        super()._validate_args()


_INSIGHTS_PATH_SUFFIX = "/insights/"


class InsightsPublishCommand(LightspeedPublishCommand):
    """Deprecated: use ``lightspeed publish`` instead."""

    SUBCOMMAND = SUBCOMMAND

    def _validate_args(self):
        _warn()
        super()._validate_args()

    def _download_lightspeed_report(self):
        path = REPORT_URI + str(self.args.report) + _INSIGHTS_PATH_SUFFIX

        response = qpc_request(
            method=GET,
            path=path,
            headers={"Accept": "application/gzip"},
        )

        if not response.ok:
            self._handle_response_error(response)

        logger.info(_(messages.LIGHTSPEED_REPORT_DOWNLOAD_SUCCESSFUL))

        output_file = NamedTemporaryFile(suffix=".tar.gz", delete=False)
        output_file_path = Path(output_file.name)
        output_file_path.write_bytes(response.content)
        return output_file_path


# END TODO
