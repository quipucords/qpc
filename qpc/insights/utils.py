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
"""Utilities for the insights module."""

from __future__ import print_function

import re
from argparse import ArgumentTypeError

# pylint: disable=no-name-in-module,import-error
from distutils.version import LooseVersion  # noqa:I202
from getpass import getpass

from qpc import messages
from qpc.translation import _
from qpc.utils import check_if_prompt_is_not_empty


class InsightsCommands:
    """Creates insights-client commands for qpc client."""

    def __init__(self, no_gpg=False):
        """Set class variables.

        Args:
            no_gpg (bool): used to build insights client command without
            requiring GNU Privacy Guard.
        """
        self.no_gpg = no_gpg
        # mime type for QPC report data for uploading to insights
        self.content_type = "application/vnd.redhat.qpc.insights+tgz"

    def build_base(self):
        """Will create a base used for creating insights commands."""
        if self.no_gpg:
            return ["sudo", "BYPASS_GPG=True", "insights-client", "--no-gpg"]
        return ["sudo", "insights-client"]

    def upload(self, tar_name):
        """Will create a command for uploading tar.gz files to insights."""
        upload_command = self.build_base()
        upload_command.append("--payload=" + tar_name)
        upload_command.append("--content-type=" + self.content_type)
        return upload_command

    def test_connection(self):
        """Will create a command that can test the connection to insights."""
        test_command = self.build_base()
        test_command.append("--test-connection")
        return test_command

    def version(self):
        """Will create a command that gathers versions."""
        version_command = self.build_base()
        version_command.append("--version")
        return version_command


def check_insights_install(streamdata):
    """Will check stream data for failure clause."""
    failures = ["command not found", "No module named 'insights'"]
    for fail in failures:
        if fail in str(streamdata):
            return False
    return True


def check_successful_upload(streamdata):
    """Will check stream data for success clause."""
    success = _(messages.REPORT_INSIGHTS_REPORT_SUCCESSFULLY_UPLOADED)
    if success in str(streamdata):
        return True
    return False


def check_insights_version(streamdata, required_client, required_core):
    """Will check versions in streamdata to match requirements."""
    check = {"results": True}
    stream_info = {}
    required_types = ["client", "core"]
    for value in streamdata.split("\n"):
        try:
            insights_type, insights_version = value.replace(" ", "").lower().split(":")
            if insights_type in required_types:
                stream_info[insights_type] = insights_version
        except ValueError:
            pass
    if sorted(stream_info.keys()) != sorted(required_types):
        error_msg = "Could not find versions for client or core."
        return {"error": error_msg, "results": False}
    for stream_type in required_types:
        stream_version = stream_info[stream_type]
        requirement = required_client if stream_type == "client" else required_core
        if LooseVersion(stream_version) < LooseVersion(requirement):
            check[stream_type] = stream_version
            check["results"] = False
    return check


def format_subprocess_stderr(process):
    """Will search the subprocess for the byte string and format it."""
    info_tuple = process.communicate()
    byte_string = None
    for result in info_tuple:
        if result:
            byte_string = result.decode("utf-8").strip("\n")
    return byte_string


def format_upload_success(streamdata):
    """Will parse the streamdata to retrieve helpful output."""
    try:
        stream_list = streamdata.split("\n")
        return stream_list[2]
    except IndexError:
        return streamdata


def validate_host(arg):
    """Validate hostname syntax.

    :param arg: a string
    :returns: the validated argument
    :raises: ArgumentTypeError, if argument is invalid
    """
    host_re = re.compile(
        r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*"
        r"([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
    )
    if host_re.search(arg) is None:
        raise ArgumentTypeError(f"Host value {arg} should be a valid hostname")
    return arg


def validate_username_and_password(arg):
    """Validate password and username syntax.

    :param arg: a string
    :returns: The validated argument
    :raises: ArgumentTypeError, if argument is invalid
    """
    argument_re = re.compile(r"^\S+$")
    if argument_re.search(arg) is None:
        raise ArgumentTypeError("The argument value is invalid.")
    return arg


def build_insights_login_config_dict(args):
    """Construct login config dict from command line arguments.

    :param args: the command line arguments
    :returns: insights login config dict
    """
    config_dict = {}
    config_dict["username"] = args.username
    if getattr(args, "password", None):
        password_prompt = getpass(messages.INSIGHTS_LOGIN_PASSWORD)
        check_if_prompt_is_not_empty(password_prompt)
        validate_username_and_password(password_prompt)
        config_dict["password"] = password_prompt
    return config_dict
