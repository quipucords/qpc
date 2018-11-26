#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test utilities for the CLI module."""

import contextlib
import io
import json
import sys
import tarfile


DEFAULT_CONFIG = {'host': '127.0.0.1', 'port': 8000, 'use_http': True}


# pylint: disable=too-few-public-methods
class HushUpStderr():
    """Class used to quiet standard error output."""

    def write(self, stream):
        """Ignore standard error output."""
        pass


@contextlib.contextmanager
def redirect_stdout(stream):
    """Run a code block, capturing stdout to the given stream."""
    old_stdout = sys.stdout
    try:
        sys.stdout = stream
        yield
    finally:
        sys.stdout = old_stdout


def create_tar_buffer(files_data):
    """Gernerate a file buffer based off a dictionary."""
    if not isinstance(files_data, (dict,)) or files_data.keys() is 0:
        return None
    if not all(isinstance(v, (str, dict)) for v in files_data.values()):
        return None
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar_file:
        for file_name, file_content in files_data.items():
            if file_name.endswith('json'):
                file_buffer = \
                    io.BytesIO(json.dumps(file_content).encode('utf-8'))
            elif file_name.endswith('csv'):
                file_buffer = io.BytesIO(file_content.encode('utf-8'))
            else:
                return None
            info = tarfile.TarInfo(name=file_name)
            info.size = len(file_buffer.getvalue())
            tar_file.addfile(tarinfo=info, fileobj=file_buffer)
    tar_buffer.seek(0)
    return tar_buffer.getvalue()
