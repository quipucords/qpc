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
