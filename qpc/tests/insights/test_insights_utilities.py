"""Test insights utilities functions."""
from argparse import ArgumentTypeError

import pytest

from qpc.insights.utils import validate_host


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
    with pytest.raises(ArgumentTypeError):
        validate_host(argument)


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
