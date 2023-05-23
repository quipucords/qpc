"""File to hold release constants."""
from . import __package__version__

VERSION = __package__version__
AUTHOR = "QPC Team"
AUTHOR_EMAIL = "qpc@redhat.com"
PKG_NAME = "qpc"
ENTRYPOINT = f"{PKG_NAME}=qpc.__main__:main"
URL = "https://github.com/quipucords/qpc"
