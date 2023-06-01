"""Common module for handling request calls to the server."""

import json
import sys

import requests
from packaging.version import Version

from qpc import messages
from qpc.release import PKG_NAME
from qpc.translation import _
from qpc.utils import (
    CONFIG_HOST_KEY,
    CONFIG_PORT_KEY,
    CONFIG_USE_HTTP,
    QPC_MIN_SERVER_VERSION,
    get_server_location,
    get_ssl_verify,
    handle_error_response,
    log_request_info,
    logger,
    read_client_token,
    read_server_config,
)

# Need to determine how we get this information; config file at install?

POST = "POST"
GET = "GET"
PATCH = "PATCH"
DELETE = "DELETE"
PUT = "PUT"

CONNECTION_ERROR_MSG = messages.CONNECTION_ERROR_MSG

try:
    exception_class = json.decoder.JSONDecodeError
except AttributeError:
    exception_class = ValueError


def handle_general_errors(response, min_server_version):
    """Handle general errors.

    :param response: The response object.
    :returns: The response object.
    """
    server_version = response.headers.get("X-Server-Version")
    if not server_version:
        server_version = QPC_MIN_SERVER_VERSION

    if "0.0.0" not in server_version and Version(server_version) < Version(
        min_server_version
    ):
        logger.error(
            _(messages.SERVER_TOO_OLD_FOR_CLI),
            {"min_version": min_server_version, "current_version": server_version},
        )
        sys.exit(1)

    token_expired = {"detail": "Token has expired"}
    response_data = None
    try:
        response_data = response.json()
    except exception_class:
        pass

    if response.status_code == 401:
        handle_error_response(response)
        logger.error(_(messages.SERVER_LOGIN_REQUIRED), PKG_NAME)
        sys.exit(1)
    elif response.status_code == 400 and response_data == token_expired:
        handle_error_response(response)
        logger.error(_(messages.SERVER_LOGIN_REQUIRED), PKG_NAME)
        sys.exit(1)
    elif response.status_code == 500:
        handle_error_response(response)
        logger.error(_(messages.SERVER_INTERNAL_ERROR))
        sys.exit(1)

    return response


def post(url, payload, headers=None):
    """Post JSON payload to the given url.

    :param url: the server, port, and path
    (i.e. http://127.0.0.1:8000/api/v1/scans/)
    :param payload: dictionary of payload to be posted
    :returns: reponse object
    """
    ssl_verify = get_ssl_verify()
    return requests.post(url, json=payload, headers=headers, verify=ssl_verify)


def get(url, params=None, headers=None):
    """Get JSON data from the given url.

    :param url: the server, port, and path
    (i.e. http://127.0.0.1:8000/api/v1/credentials)
    :param params: uri encoding params (i.e. ?param1=hello&param2=world)
    :returns: reponse object
    """
    ssl_verify = get_ssl_verify()
    return requests.get(url, params=params, headers=headers, verify=ssl_verify)


def patch(url, payload, headers=None):
    """Patch JSON payload to the given url.

    :param url: the server, port, and path
    (i.e. http://127.0.0.1:8000/api/v1/credentials/1)
    :param payload: dictionary of payload to be posted
    :returns: reponse object
    """
    ssl_verify = get_ssl_verify()
    return requests.patch(url, json=payload, headers=headers, verify=ssl_verify)


def delete(url, headers=None):
    """Delete the item with the given url.

    :param url: the server, port, and path
    (i.e. http://127.0.0.1:8000/api/v1/credentials/1)
    :returns: reponse object
    """
    ssl_verify = get_ssl_verify()
    return requests.delete(url, headers=headers, verify=ssl_verify)


def put(url, payload, headers=None):
    """Put JSON payload to the given url.

    :param url: the server, port, and path
    (i.e. http://127.0.0.1:8000/api/v1/credentials/1)
    :param payload: dictionary of payload to be posted
    :returns: reponse object
    """
    ssl_verify = get_ssl_verify()
    return requests.put(url, json=payload, headers=headers, verify=ssl_verify)


methods = {
    "POST": post,
    "GET": get,
    "PATCH": patch,
    "DELETE": delete,
    "PUT": put,
}


def request(  # noqa: PLR0913
    method,
    path,
    params=None,
    payload=None,
    parser=None,
    headers=None,
    min_server_version=QPC_MIN_SERVER_VERSION,
):
    """Create a generic handler for passing to specific request methods.

    :param method: the request method to execute
    :param path: path after server and port (i.e. /api/v1/credentials)
    :param params: uri encoding params (i.e. ?param1=hello&param2=world)
    :param payload: dictionary of payload to be posted
    :param parser: parser for printing usage on failure
    :param headers: headers to include
    :param min_server_version: min qpc server version allowed
    :returns: reponse object
    :raises: AssertionError error if method is not supported
    """
    # grab the cli command for the log if the parser is provided
    log_command = None
    if parser is not None:
        log_command = parser.prog
    token = read_client_token()
    url = get_server_location() + path
    req_headers = headers or {}
    if token:
        req_headers["Authorization"] = f"Token {token}"

    if method not in methods:
        logger.error("Unsupported request method %s", method)
        parser.print_help()
        sys.exit(1)

    try:
        result = perform_request(
            method, url, params, payload, req_headers, min_server_version
        )

    except (requests.exceptions.ConnectionError, requests.exceptions.SSLError):
        handle_connection_error()
        sys.exit(1)

    log_request_info(
        method, log_command, url, decode_response_json(result), result.status_code
    )
    return result


def handle_connection_error():
    """Log connection error."""
    config = read_server_config()
    if config is not None:
        protocol = "https"
        host = config.get(CONFIG_HOST_KEY)
        port = config.get(CONFIG_PORT_KEY)
        if config.get(CONFIG_USE_HTTP):
            protocol = "http"
        logger.error(
            _(CONNECTION_ERROR_MSG), {"protocol": protocol, "host": host, "port": port}
        )
    logger.error(_(messages.SERVER_CONFIG_REQUIRED), PKG_NAME)


def perform_request(  # noqa: PLR0913
    method,
    url,
    params=None,
    payload=None,
    req_headers=None,
    min_server_version=QPC_MIN_SERVER_VERSION,
):
    """Perform the api request and return the response."""
    request_method = methods[method]
    if method == "GET":
        return handle_general_errors(
            request_method(url, params, req_headers), min_server_version
        )
    if method == "DELETE":
        return handle_general_errors(
            request_method(url, req_headers), min_server_version
        )
    return handle_general_errors(
        request_method(url, payload, req_headers), min_server_version
    )


def decode_response_json(response):
    """Return either a json or text to avoid saving binary to logs."""
    try:
        return response.json()
    except ValueError:
        return "<encoded blob ignored>"
