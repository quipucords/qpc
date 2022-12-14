#!/usr/bin/env python
#
# Copyright (c) 2018-2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Constants for the Insights commands."""

SUBCOMMAND = "insights"
UPLOAD = "upload"
CONFIG = "config"
ADD_LOGIN = "add_login"
PUBLISH = "publish"

REPORT_URI = "/api/v1/reports/"
INSIGHTS_PATH_SUFFIX = "/insights/"
# Note the the insights version check does not handle if versions equal
CLIENT_VERSION = "3.0.3-1"
CORE_VERSION = "3.0.71-1"

CONTENT_TYPE = "application/vnd.redhat.qpc.tar+tgz"
INGRESS_REPORT_URI = "/api/ingress/v1/upload"
