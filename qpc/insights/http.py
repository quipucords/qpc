# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
"""HTTP Client for console.redhat.com."""
from urllib.parse import urljoin

import requests


class InsightsClient(requests.Session):
    """An HTTP Client for C.RH.C. based on requests Session class."""

    def __init__(self, *, base_url=None, auth=None, **kwargs):
        """
        Initialize ApiClient.

        base_url: will be prepended to all requests urls
        auth: basic auth, receives a tuple, insights username and password
        """
        super().__init__(**kwargs)
        self.base_url = base_url
        self.auth = auth

    def request(self, method, url, *args, **kwargs):
        """Prepare a request and send it."""
        request_url = urljoin(self.base_url, url) if self.base_url else url
        return super().request(method, request_url, *args, **kwargs)
