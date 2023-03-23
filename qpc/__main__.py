"""Main qpc entrypoint."""

import gettext

from qpc.cli import CLI


def main():
    """Execute qpc CLI."""
    gettext.install("qpc")
    CLI().main()


if __name__ == "__main__":
    main()
