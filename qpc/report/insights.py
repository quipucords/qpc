# TODO: remove after 2.10 release when CI no longer uses `report insights`
# To remove: git revert <this-commit-sha> (see DISCOVERY-1571)
"""Deprecated: use `report lightspeed` instead."""

import warnings
from logging import getLogger

from qpc import report
from qpc.report.lightspeed import ReportLightspeedCommand

logger = getLogger(__name__)


class ReportInsightsCommand(ReportLightspeedCommand):
    """Deprecated alias for ReportLightspeedCommand.

    .. deprecated::
        Use ``report lightspeed`` instead. This alias will be removed after the
        2.10 release once CI is updated to use the new command name.
    """

    ACTION = report.INSIGHTS

    def _validate_args(self):
        warnings.warn(
            "`report insights` is deprecated and will be removed after the 2.10 "
            "release. Use `report lightspeed` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        logger.warning(
            "Deprecated command `report insights` called. "
            "Use `report lightspeed` instead."
        )
        super()._validate_args()
        self.req_path = self.req_path.replace(
            report.LIGHTSPEED_PATH_SUFFIX, report.INSIGHTS_PATH_SUFFIX
        )


# END TODO
