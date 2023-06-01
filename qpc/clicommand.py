"""Base CLI Command Class."""

import sys

from qpc.request import request
from qpc.utils import QPC_MIN_SERVER_VERSION, handle_error_response, log_args


class CliCommand:
    """Base class for all sub-commands."""

    def __init__(  # noqa: PLR0913
        self, subcommand, action, parser, req_method, req_path, success_codes
    ):
        """Create cli command base object."""
        self.subcommand = subcommand
        self.action = action
        self.parser = parser
        self.req_method = req_method
        self.req_path = req_path
        self.success_codes = success_codes
        self.args = None
        self.req_payload = None
        self.req_params = None
        self.req_headers = None
        self.response = None

        # If you add or change API, you must update these versions
        # this includes self.min_server_version
        self.min_server_version = QPC_MIN_SERVER_VERSION

    def _validate_args(self):
        """Sub-commands can override."""

    def _build_req_params(self):
        """Sub-commands can override to construct request parameters."""

    def _build_data(self):
        """Sub-commands can define to construct request payload."""

    def _handle_response_error(self, response=None):
        """Sub-commands can override this method to perform error handling."""
        handle_error_response(response or self.response)
        sys.exit(1)

    def _handle_response_success(self):
        """Sub-commands can override to perform success handling."""

    def _do_command(self):
        """Execute command flow.

        Sub-commands define this method to perform the
        required action once all options have been verified.
        """
        self._build_req_params()
        self._build_data()
        self.response = request(
            method=self.req_method,
            path=self.req_path,
            params=self.req_params,
            payload=self.req_payload,
            headers=self.req_headers,
            parser=self.parser,
            min_server_version=self.min_server_version,
        )

        if self.response.status_code not in self.success_codes:
            # handle error cases
            self._handle_response_error()
        else:
            self._handle_response_success()

    def main(self, args):
        """Trigger main command flow.

        The method that does a basic check for command
        validity and set's the process in motion.
        """
        self.args = args
        self._validate_args()
        log_args(self.args)

        self._do_command()
