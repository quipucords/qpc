"""File to hold release constants."""

import os
import subprocess
from pathlib import Path

from . import __package__version__

VERSION = __package__version__
AUTHOR = "QPC Team"
AUTHOR_EMAIL = "qpc@redhat.com"
# BEGIN IMPORTANT NOTE: Do not change these lines.
# Downstream builds may patch these lines to change the program name.
# See also: https://issues.redhat.com/browse/DISCOVERY-785
QPC_VAR_PROGRAM_NAME = os.environ.get("QPC_VAR_PROGRAM_NAME", "qpc")
ENTRYPOINT = f"{QPC_VAR_PROGRAM_NAME}=qpc.__main__:main"
# END IMPORTANT NOTE.
URL = "https://github.com/quipucords/qpc"


def get_current_sha1() -> str:
    """Get the running code's current git commit SHA-1."""
    if qpc_commit := os.environ.get("QPC_COMMIT", "").strip():
        return qpc_commit
    try:
        repo_root = Path(__file__).absolute().parent.parent
        git_env = os.environ.copy()
        git_env["LANG"] = "C"
        git_env["LC_ALL"] = "C"
        git_result = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            env=git_env,
            cwd=repo_root,
            capture_output=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        # FileNotFoundError raises when `git` program not found.
        # CalledProcessError raises when `git` has non-zero return code.
        return "UNKNOWN"
    git_sha1 = git_result.stdout.decode().split("\n")[0]
    try:
        int(git_sha1, 16)
    except ValueError:
        # ValueError raises when the string does not contain a hexadecimal value.
        return "UNKNOWN"
    return git_sha1
