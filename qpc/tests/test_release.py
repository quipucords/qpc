"""Test the `qpc.release` module."""

import subprocess
from unittest import mock

from qpc import release


def test_get_current_sha1_uses_env_var():
    """Test getting the "current" commit from the environment variable."""
    expected_value = "DEADBEEF"
    with mock.patch.dict(release.os.environ, {"QPC_COMMIT": expected_value}):
        actual_value = release.get_current_sha1()
    assert actual_value == expected_value, "failed to get value from environment"


@mock.patch("qpc.release.subprocess.run")
@mock.patch.dict(release.os.environ, {"QPC_COMMIT": ""})
def test_get_current_sha1_uses_git(mock_run):
    """Test getting the actual current commit from git."""
    expected_value = "DECAFBAD"
    mock_run.return_value.stdout = expected_value.encode()
    actual_value = release.get_current_sha1()
    assert actual_value == expected_value, "failed to get SHA-1 value from git"


@mock.patch("qpc.release.subprocess.run")
@mock.patch.dict(release.os.environ, {"QPC_COMMIT": ""})
def test_get_current_sha1_unknown_no_git_repo(mock_run):
    """Test trying to get the SHA-1 when the env var and git repo are both missing."""
    expected_value = "UNKNOWN"
    mock_run.side_effect = subprocess.CalledProcessError(returncode=420, cmd="git")
    actual_value = release.get_current_sha1()
    assert actual_value == expected_value, "failed to get UNKNOWN value"


@mock.patch("qpc.release.subprocess.run")
@mock.patch.dict(release.os.environ, {"QPC_COMMIT": ""})
def test_get_current_sha1_unknown_unexpected_git_stdout(mock_run):
    """Test trying to get the SHA-1 when the git outputs a non-hexadecimal value."""
    expected_value = "UNKNOWN"
    mock_run.return_value.stdout = "this is not hexadecimal".encode()
    actual_value = release.get_current_sha1()
    assert actual_value == expected_value, "failed to get UNKNOWN value"
