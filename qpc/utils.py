#!/usr/bin/env python
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
"""QPC Command Line utilities."""

from __future__ import print_function

import io
import json
import logging
import os
import sys
import tarfile

from qpc import messages
from qpc.translation import _ as t

QPC_PATH = 'qpc'
CONFIG_HOME_PATH = '~/.config/'
DATA_HOME_PATH = '~/.local/share/'
CONFIG_HOME = os.path.expanduser(CONFIG_HOME_PATH)
DATA_HOME = os.path.expanduser(DATA_HOME_PATH)
CONFIG_DIR = os.path.join(CONFIG_HOME, QPC_PATH)
DATA_DIR = os.path.join(DATA_HOME, QPC_PATH)
QPC_LOG = os.path.join(DATA_DIR, "qpc.log")
QPC_SERVER_CONFIG = os.path.join(CONFIG_DIR, "server.config")
QPC_CLIENT_TOKEN = os.path.join(CONFIG_DIR, "client_token")
INSIGHTS_CONFIG = os.path.join(CONFIG_DIR, "insights.config")
INSIGHTS_LOGIN_CONFIG = os.path.join(CONFIG_DIR, "insights_login_config")

CONFIG_HOST_KEY = 'host'
CONFIG_PORT_KEY = 'port'
CONFIG_USE_HTTP = 'use_http'
CONFIG_SSL_VERIFY = 'ssl_verify'
CONFIG_REQUIRE_TOKEN = 'require_token'

INSIGHTS_CONFIG_USERNAME_KEY = "username"
INSIGHTS_CONFIG_PASSWORD_KEY = "password"

DEFAULT_HOST_INSIGHTS_CONFIG = "console.redhat.com"
DEFAULT_PORT_INSIGHTS_CONFIG = 443
DEFAULT_USE_HTTP_INSIGHTS_CONFIG = False

DEFAULT_INSIGHTS_CONFIG = {
    CONFIG_HOST_KEY: DEFAULT_HOST_INSIGHTS_CONFIG,
    CONFIG_PORT_KEY: DEFAULT_PORT_INSIGHTS_CONFIG,
    CONFIG_USE_HTTP: DEFAULT_USE_HTTP_INSIGHTS_CONFIG,
}

LOG_LEVEL_INFO = 0

QPC_MIN_SERVER_VERSION = '0.9.0'

# pylint: disable=invalid-name
logging.captureWarnings(True)
log = logging.getLogger('qpc')


def ensure_config_dir_exists():
    """Ensure the qpc configuration directory exists."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)


def get_ssl_verify():
    """Obtain configuration for using ssl cert verification."""
    config = read_server_config()
    if config is None:
        # No configuration written to server.config
        return None
    ssl_verify = config.get(CONFIG_SSL_VERIFY, False)
    if not ssl_verify:
        ssl_verify = False
    return ssl_verify


def get_server_location():
    """Build URI from server configuration.

    :returns: The URI to the sonar server.
    """
    config = read_server_config()
    if config is None:
        # No configuration written to server.config
        return None

    use_http = config.get(CONFIG_USE_HTTP, False)
    protocol = 'https'
    if use_http:
        protocol = 'http'

    server_location = '{}://{}:{}'.format(
        protocol, config[CONFIG_HOST_KEY], config[CONFIG_PORT_KEY])
    return server_location


try:
    exception_class = json.decoder.JSONDecodeError
except AttributeError:
    exception_class = ValueError


def read_client_token():
    """Retrieve client token for sonar server.

    :returns: The client token or None
    """
    if not os.path.exists(QPC_CLIENT_TOKEN):
        return None

    token = None
    with open(QPC_CLIENT_TOKEN) as client_token_file:
        try:
            token_json = json.load(client_token_file)
            token = token_json.get('token')
        except exception_class:
            pass

        return token


def read_require_auth():
    """Determine if CLI should require token.

    :returns: True is auth token required.
    """
    config = read_server_config()
    if config is None:
        # No configuration so True
        return True
    return config.get(CONFIG_REQUIRE_TOKEN)


def read_insights_config():
    """Retrieve insights configuration.

    :returns: The validated dictionary with configuration
    """
    if not os.path.exists(INSIGHTS_CONFIG):
        return DEFAULT_INSIGHTS_CONFIG

    with open(INSIGHTS_CONFIG, encoding="utf-8") as insights_config_file:
        try:
            config = json.load(insights_config_file)
        except exception_class:
            return DEFAULT_INSIGHTS_CONFIG
    insights_config = dict(DEFAULT_INSIGHTS_CONFIG, **config)
    return insights_config


def read_server_config():
    """Retrieve configuration for sonar server.

    :returns: The validate dictionary with configuration
    """
    # pylint: disable=too-many-return-statements
    if not os.path.exists(QPC_SERVER_CONFIG):
        log.error('Server config %s was not found.',
                  QPC_SERVER_CONFIG)
        return None

    with open(QPC_SERVER_CONFIG) as server_config_file:
        try:
            config = json.load(server_config_file)
        except exception_class:
            return None

        host = config.get(CONFIG_HOST_KEY)
        port = config.get(CONFIG_PORT_KEY)
        use_http = config.get(CONFIG_USE_HTTP)
        ssl_verify = config.get(CONFIG_SSL_VERIFY, False)
        require_token = config.get(CONFIG_REQUIRE_TOKEN)

        host_empty = host is None or host == ''
        port_empty = port is None or port == ''

        if host_empty or port_empty:
            return None

        if not isinstance(host, str):
            log.error('Server config %s has invalid value for host %s',
                      QPC_SERVER_CONFIG, host)
            return None

        if not isinstance(port, int):
            log.error('Server config %s has invalid value for port %s',
                      QPC_SERVER_CONFIG, port)
            return None

        if use_http is None:
            use_http = True

        if require_token is None:
            require_token = True

        if not isinstance(use_http, bool):
            log.error('Server config %s has invalid value for use_http %s',
                      QPC_SERVER_CONFIG, use_http)
            return None

        if not isinstance(require_token, bool):
            log.error('Server config %s has invalid value for require_token %s',
                      QPC_SERVER_CONFIG, require_token)
            return None

        if (ssl_verify is not None and
                not isinstance(ssl_verify, bool) and
                not isinstance(ssl_verify, str)):
            log.error('Server config %s has invalid value for ssl_verify %s',
                      QPC_SERVER_CONFIG, ssl_verify)
            return None

        if (ssl_verify is not None and
                isinstance(ssl_verify, str) and
                not os.path.exists(ssl_verify)):
            log.error('Server config %s has invalid path for ssl_verify %s',
                      QPC_SERVER_CONFIG, ssl_verify)
            return None

        return {CONFIG_HOST_KEY: host,
                CONFIG_PORT_KEY: port,
                CONFIG_USE_HTTP: use_http,
                CONFIG_SSL_VERIFY: ssl_verify,
                CONFIG_REQUIRE_TOKEN: require_token}


def write_config(config_file_path, config_dict):
    """Write configuration to config file.

    :param config_dict: dict containing configuration info
    :param config_file_path: path to configuration file
    """
    ensure_config_dir_exists()

    with open(config_file_path, "w", encoding="utf-8") as config_file:
        json.dump(config_dict, config_file, indent=4)


def write_server_config(server_config):
    """Write server configuration to server.config.

    :param server_config: dict containing server configuration
    """
    write_config(QPC_SERVER_CONFIG, server_config)


def write_insights_login_config(login_config):
    """Write insights login configuration to insights_login_config.

    :param login_config: dict containing insights login configuration
    """
    write_config(INSIGHTS_LOGIN_CONFIG, login_config)


def write_insights_config(insights_config):
    """Write insights configuration to insights.config.

    :param insights_config: dict containing insights configuration
    """
    write_config(INSIGHTS_CONFIG, insights_config)


def read_insights_login_config():
    """Retrieve insights login configuration.

    :returns: The validated dictionary with configuration
    """
    if not os.path.exists(INSIGHTS_LOGIN_CONFIG):
        log.error("Insights login config was not found.")
        return None

    with open(INSIGHTS_LOGIN_CONFIG, encoding="utf-8") as insights_login_config_file:
        try:
            config = json.load(insights_login_config_file)
        except exception_class:
            return None

    username = config.get(INSIGHTS_CONFIG_USERNAME_KEY)
    password = config.get(INSIGHTS_CONFIG_PASSWORD_KEY)

    return {
        INSIGHTS_CONFIG_USERNAME_KEY: username,
        INSIGHTS_CONFIG_PASSWORD_KEY: password,
    }


def write_client_token(client_token):
    """Write client token to file client_token.

    :param client_token: dict containing client_token
    """
    ensure_config_dir_exists()

    with open(QPC_CLIENT_TOKEN, 'w') as configFile:
        json.dump(client_token, configFile)


def delete_client_token():
    """Remove file client_token."""
    ensure_config_dir_exists()
    try:
        os.remove(QPC_CLIENT_TOKEN)
    except FileNotFoundError:
        pass


def ensure_data_dir_exists():
    """Ensure the qpc data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def setup_logging(verbosity):
    """Set up Python logging for qpc.

    Must be run after ensure_data_dir_exists().

    :param verbosity: verbosity level, as measured in -v's on the command line.
        Can be None for default.
    """
    if verbosity == LOG_LEVEL_INFO:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    # Using basicConfig here means that all log messages, even
    # those not coming from qpc, will go to the log file
    logging.basicConfig(filename=QPC_LOG, format='%(asctime)s - %(name)s - '
                                                 '%(levelname)s - %(message)s')
    # but we only adjust the log level for the 'qpc' logger.
    log.setLevel(log_level)
    # the StreamHandler sends warnings and above to stdout, but
    # only for messages going to the 'qpc' logger, i.e. QPC
    # output.
    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(logging.ERROR)
    log.addHandler(stderr_handler)


def log_request_info(method, command, url, response_json, response_code):
    """Log the information regarding the request being made.

    :param method: the method being called (ie. POST)
    :param command: the command being used (ie. qpc cred add)
    :param url: the server, port, and path
    (i.e. http://127.0.0.1:8000/api/v1/credentials/1)
    :param response_json: the response returned from the request
    :param response_code: the status code being returned (ie. 200)
    """
    message = 'Method: "%s", Command: "%s", URL: "%s", '\
              'Response: "%s", Status Code: "%s'
    log.info(message, method, command, url,
             response_json, response_code)


def log_args(args):
    """Log the arguments for each qpc command.

    :param args: the arguments provided to the qpc command
    """
    message = 'Args: "%s"'
    log.info(message, args)


def handle_error_response(response):
    """Print errors from response data.

    :param response: The response object with a dictionary of keys and
        lists of errors
    """
    try:
        response_data = response.json()
        if isinstance(response_data, str):
            log.error('Error: %s', str(response_data))
        if isinstance(response_data, dict):
            for err_key, err_cases in response_data.items():
                error_context = 'Error'
                if err_key not in ['non_field_errors', 'detail', 'options']:
                    error_context = err_key
                if isinstance(err_cases, str):
                    log.error('%s: %s', error_context, err_cases)
                elif isinstance(err_cases, dict):
                    log.error('%s: %s', error_context, err_cases)
                else:
                    for err_msg in err_cases:
                        log.error('%s: %s', error_context, err_msg)
        elif isinstance(response_data, list):
            for err in response_data:
                log.error('Error: %s', err)
        else:
            log.error('Error: %s', str(response_data))
    except exception_class:
        pass


def pretty_print(json_data):
    """Provide pretty printing of output json data.

    :param json_data: the json data to pretty print
    :returns: the pretty print string of the json data
    """
    return json.dumps(json_data, sort_keys=True, indent=4,
                      separators=(',', ': '))


# Read in a file and make it a list
def read_in_file(filename):
    """Read values from file into a list object. Expecting newline delimited.

    :param filename: the filename to read
    :returns: the list of values found in the file
    :raises: ValueError if incoming value is not a file that could be found
    """
    result = None
    input_path = os.path.expanduser(os.path.expandvars(filename))
    # pylint: disable=no-else-return
    if os.path.isfile(input_path):
        try:
            with open(input_path, 'r') as in_file:
                result = in_file.read().splitlines()
        except EnvironmentError as err:
            err_msg = t(messages.READ_FILE_ERROR % (input_path, err))
            log.error(err_msg)
        return result
    else:
        raise ValueError(t(messages.NOT_A_FILE % input_path))


def validate_write_file(filename, param_name):
    """Write content to a file.

    :param filename: the filename to write
    :param param_name: the parameter name that provided
    the filename
    :raises: ValueError for validation errors
    """
    input_path = os.path.expanduser(os.path.expandvars(filename))
    if not input_path:
        raise ValueError(
            t(messages.REPORT_OUTPUT_CANNOT_BE_EMPTY % param_name))
    if os.path.isdir(input_path):
        raise ValueError(
            t(messages.REPORT_OUTPUT_IS_A_DIRECTORY %
              (param_name, input_path)))
    directory = os.path.dirname(input_path)
    if directory and not os.path.exists(directory):
        raise ValueError(
            t(messages.REPORT_DIRECTORY_DOES_NOT_EXIST % directory))


def write_file(filename, content, binary=False):
    """Write content to a file.

    :param filename: the filename to write
    :param content: the file content to write
    :raises: EnvironmentError if file cannot be written
    """
    result = None
    input_path = os.path.expanduser(os.path.expandvars(filename))
    mode = 'w'
    if binary:
        mode = 'wb'
    with open(input_path, mode) as out_file:
        out_file.write(content)
    return result


def extract_json_from_tar(fileobj_content, print_pretty=True):
    """Extract json data from tar.gz bytes.

    :param fileobj_content: BytesIo object with tarball of json dict
    :param print_pretty: Boolean to determine whether to return pretty
        print json (str) or normal json
    """
    tar = tarfile.open(fileobj=io.BytesIO(fileobj_content), mode='r:gz')
    json_file = tar.getmembers()[0]
    tar_info = tar.extractfile(json_file)
    json_data = json.loads(tar_info.read().decode('utf-8'))
    if print_pretty:
        return pretty_print(json_data)
    return json_data


def create_tar_buffer(files_data):
    """Generate a file buffer based off a dictionary."""
    if not isinstance(files_data, (dict,)):
        print('ERROR: files_data is not a dict')
        return None
    if not all(isinstance(v, (str, dict)) for v in files_data.values()):
        print('ERROR: Not correct structure for tar')
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
                print('ERROR: unknown file extension')
                return None
            info = tarfile.TarInfo(name=file_name)
            info.size = len(file_buffer.getvalue())
            tar_file.addfile(tarinfo=info, fileobj=file_buffer)
    tar_buffer.seek(0)
    return tar_buffer.getvalue()


def check_extension(extension, path):
    """Check if .json is in the file extension."""
    if extension not in path:
        print(t(messages.OUTPUT_FILE_TYPE % extension))
        sys.exit(1)
