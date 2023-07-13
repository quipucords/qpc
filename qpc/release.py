"""File to hold release constants."""
import os
from pathlib import Path

import git

from . import __package__version__

VERSION = __package__version__
AUTHOR = "QPC Team"
AUTHOR_EMAIL = "qpc@redhat.com"
QPC_VAR_PROGRAM_NAME = os.environ.get("QPC_VAR_PROGRAM_NAME", "qpc")
ENTRYPOINT = f"{QPC_VAR_PROGRAM_NAME}=qpc.__main__:main"
URL = "https://github.com/quipucords/qpc"


def get_current_sha1() -> str:
    """Get the running code's current git commit SHA-1."""
    if qpc_commit := os.environ.get("QPC_COMMIT", "").strip():
        return qpc_commit
    try:
        repo_root = Path(__file__).absolute().parent.parent
        repo = git.Repo(repo_root)
    except git.exc.InvalidGitRepositoryError:
        return "UNKNOWN"
    return repo.rev_parse("HEAD").hexsha
