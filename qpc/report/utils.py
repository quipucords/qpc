"""Helper functions for processing reports."""

import json
from logging import getLogger
from pathlib import Path

from qpc import messages
from qpc.translation import _

logger = getLogger(__name__)


SOURCES_KEY = "sources"
FACTS_KEY = "facts"
SERVER_ID_KEY = "server_id"
REPORT_VERSION_KEY = "report_version"
REPORT_TYPE_KEY = "report_type"
DEFAULT_REPORT_VERSION = "0.0.44.legacy"
DETAILS_REPORT_TYPE = "details"


def validate_and_create_json(file):
    """Validate the details report file and create sources JSON.

    :param file: str containing path for details report file
    :return: sources dictionary or None if there were validation errors
    """
    logger.info(_(messages.REPORT_UPLOAD_VALIDATE_JSON), file)
    sources = None
    file = Path(file)
    if file.is_file():
        details_report = None
        with file.open(encoding="utf-8") as details_file:
            try:
                details_report = json.load(details_file)
            except json.decoder.JSONDecodeError:
                logger.error(_(messages.REPORT_UPLOAD_FILE_INVALID_JSON), file)
                return None

            # validate version type
            file_report_version = details_report.get(REPORT_VERSION_KEY, None)
            if not file_report_version:
                # warn about old format but continue
                logger.error(_(messages.REPORT_MISSING_REPORT_VERSION), file)
                file_report_version = DEFAULT_REPORT_VERSION

            file_report_type = details_report.get(REPORT_TYPE_KEY, DETAILS_REPORT_TYPE)
            if file_report_type != DETAILS_REPORT_TYPE:
                # terminate if different from details type
                logger.error(
                    _(messages.REPORT_INVALID_REPORT_TYPE),
                    {"file": file, "report_type": file_report_type},
                )
                return None

            # validate sources
            sources = details_report.get(SOURCES_KEY, None)
            if sources:
                has_error = False
                for source in sources:
                    facts = source.get(FACTS_KEY)
                    server_id = source.get(SERVER_ID_KEY)
                    if not facts:
                        logger.error(
                            _(messages.REPORT_JSON_MISSING_ATTR),
                            {"file": file, "key": FACTS_KEY},
                        )
                        has_error = True
                        break
                    if not server_id:
                        logger.error(
                            _(messages.REPORT_JSON_MISSING_ATTR),
                            {"file": file, "key": FACTS_KEY},
                        )
                        has_error = True
                        break
                    # Add version/type to all sources since merge
                    source[REPORT_TYPE_KEY] = file_report_type
                    source[REPORT_VERSION_KEY] = file_report_version

                if not has_error:
                    # Source is valid so add it
                    logger.info(_(messages.REPORT_JSON_DIR_FILE_SUCCESS), file)
                else:
                    return None
            else:
                logger.error(
                    _(messages.REPORT_JSON_MISSING_ATTR),
                    {"file": file, "key": SOURCES_KEY},
                )
                return None
    else:
        logger.error(_(messages.FILE_NOT_FOUND), file)
        return None

    return sources
