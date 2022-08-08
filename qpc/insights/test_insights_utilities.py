# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test insights utilities functions."""
from argparse import ArgumentTypeError

import pytest

from qpc.insights.utils import validate_host, validate_username_and_password


@pytest.mark.parametrize(
    "argument",
    (
        "",
        "BLYYNJABKJA3489734894T93855$$%%",
        "$%^^",
        " bla124",
        "*123456AAB ",
        " ",
    ),
)
def test_invalid_host_should_not_be_validated(argument):
    """Ensure invalid hosts are not validated."""
    with pytest.raises(ArgumentTypeError) as error:
        validate_host(argument)
    assert str(error.value) == f"Host value {argument} should be a valid hostname"


@pytest.mark.parametrize(
    "argument",
    (
        "BLYYNJABKJA3489734894T93855",
        "OOOOOOOi12345896",
        "abcdefghijklmnopqrstuvxzwy0123456789",
        "ABCDEFGHIJKLMNOPQRSTUVXZWY0123456789",
    ),
)
def test_valid_host_should_be_returned(argument):
    """Ensure valid hosts are returned."""
    validated_argument = validate_host(argument)
    assert validated_argument == argument


@pytest.mark.parametrize(
    "argument",
    (
        "",
        " ",
        "\u0008\u000C\u000D\u0009\u000B\u0000",
    ),
)
def test_invalid_passwords_and_usernames_should_not_be_validated(argument):
    """Ensure invalid passwords and usernames are not validated."""
    with pytest.raises(ArgumentTypeError) as error:
        validate_username_and_password(argument)
    assert str(error.value) == "The argument value is invalid."


@pytest.mark.parametrize(
    "argument",
    (
        "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^"
        "_`abcdefghijklmnopqrstuvwxyz{|}~",
    ),
)
def test_valid_passwords_should_be_returned(argument):
    """Ensure valid passwords are returned."""
    validated_password = validate_username_and_password(argument)
    assert validated_password == argument
