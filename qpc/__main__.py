# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
"""Main qpc entrypoint."""

import gettext

from qpc.cli import CLI


def main():
    """Execute qpc CLI."""
    gettext.install("qpc")
    CLI().main()


if __name__ == "__main__":
    main()
