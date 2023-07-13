"""Test the `qpc.release` module."""
from unittest import mock

from qpc import release


def test_get_current_sha1_uses_env_var():
    """Test getting the "current" commit from the environment variable."""
    expected_value = "DEADBEEF"
    with mock.patch.dict(release.os.environ, {"QPC_COMMIT": expected_value}):
        actual_value = release.get_current_sha1()
    assert actual_value == expected_value, "failed to get value from environment"


def test_get_current_sha1_uses_git():
    """Test getting the actual current from git."""
    expected_value = "DECAFBAD"
    with mock.patch.dict(release.os.environ, {"QPC_COMMIT": ""}), mock.patch(
        "git.Repo.rev_parse"
    ) as mock_rev_parse:
        mock_rev_parse.return_value.hexsha = expected_value
        actual_value = release.get_current_sha1()
    assert actual_value == expected_value, "failed to get SHA-1 value from git"


def test_get_current_sha1_unknown():
    """Test trying to get the SHA-1 when the env var and git repo are both missing."""
    expected_value = "UNKNOWN"
    with mock.patch.dict(release.os.environ, {"QPC_COMMIT": ""}), mock.patch(
        "git.Repo"
    ) as mock_repo_class:
        mock_repo_class.side_effect = release.git.exc.InvalidGitRepositoryError
        actual_value = release.get_current_sha1()
    assert actual_value == expected_value, "failed to get UNKNOWN value"
