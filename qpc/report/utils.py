#!/usr/bin/env python
#
# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""ReportUploadCommand is used to upload details JSON."""

from __future__ import print_function

import json
import os

from qpc import messages
from qpc.translation import _

# pylint: disable=invalid-name
try:
    json_exception_class = json.decoder.JSONDecodeError
except AttributeError:
    json_exception_class = ValueError


SOURCES_KEY = 'sources'
FACTS_KEY = 'facts'
SERVER_ID_KEY = 'server_id'
REPORT_VERSION_KEY = 'report_version'
REPORT_TYPE_KEY = 'report_type'
DEFAULT_REPORT_VERSION = '0.0.44.legacy'
DETAILS_REPORT_TYPE = 'details'


def validate_and_create_json(file):
    """Validate the details report file and create sources JSON.

    :param file: str containing path for details report file
    :return: sources dictionary or None if there were validation errors
    """
    # pylint: disable=too-many-branches,too-many-statements
    # pylint: disable=too-many-locals
    print(_(messages.REPORT_UPLOAD_VALIDATE_JSON % file))
    sources = None
    if os.path.isfile(file):
        details_report = None
        with open(file) as details_file:
            try:
                details_report = json.load(details_file)
            except json_exception_class:
                print(_(messages.REPORT_UPLOAD_FILE_INVALID_JSON % file))
                return None

            # validate version type
            file_report_version = details_report.get(
                REPORT_VERSION_KEY, None)
            if not file_report_version:
                # warn about old format but continue
                print(_(messages.REPORT_MISSING_REPORT_VERSION % file))
                file_report_version = DEFAULT_REPORT_VERSION

            file_report_type = details_report.get(
                REPORT_TYPE_KEY, DETAILS_REPORT_TYPE)
            if file_report_type != DETAILS_REPORT_TYPE:
                # terminate if different from details type
                print(_(messages.REPORT_INVALID_REPORT_TYPE %
                        (file, file_report_type)))
                return None

            # validate sources
            sources = details_report.get(SOURCES_KEY, None)
            if sources:
                has_error = False
                for source in sources:
                    facts = source.get(FACTS_KEY)
                    server_id = source.get(SERVER_ID_KEY)
                    if not facts:
                        print(_(messages.REPORT_JSON_MISSING_ATTR %
                                (file, FACTS_KEY)))
                        has_error = True
                        break
                    if not server_id:
                        print(
                            _(messages.REPORT_JSON_MISSING_ATTR % (file, SERVER_ID_KEY)))
                        has_error = True
                        break
                    # Add version/type to all sources since merge
                    source[REPORT_TYPE_KEY] = file_report_type
                    source[REPORT_VERSION_KEY] = file_report_version

                if not has_error:
                    # Source is valid so add it
                    print(_(messages.REPORT_JSON_DIR_FILE_SUCCESS %
                            file))
                else:
                    return None
            else:
                print(_(messages.REPORT_JSON_MISSING_ATTR %
                        (file, SOURCES_KEY)))
                return None
    else:
        print(_(messages.FILE_NOT_FOUND % file))
        return None

    return sources
