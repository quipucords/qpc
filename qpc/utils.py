"""QPC Command Line utilities."""

import io
import json
import logging
import os
import sys
import tarfile
from collections import defaultdict
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from qpc import messages
from qpc.insights.exceptions import QPCEncryptionKeyError, QPCLoginConfigError
from qpc.translation import _ as t

QPC_PATH = "qpc"
CONFIG_HOME_PATH = Path("~/.config/")
DATA_HOME_PATH = Path("~/.local/share/")
CONFIG_HOME = CONFIG_HOME_PATH.expanduser()
DATA_HOME = DATA_HOME_PATH.expanduser()
CONFIG_DIR = CONFIG_HOME / QPC_PATH
DATA_DIR = DATA_HOME / QPC_PATH
QPC_LOG = DATA_DIR / "qpc.log"
QPC_SERVER_CONFIG = CONFIG_DIR / "server.config"
QPC_CLIENT_TOKEN = CONFIG_DIR / "client_token"
INSIGHTS_CONFIG = CONFIG_DIR / "insights.config"
INSIGHTS_AUTH_TOKEN = CONFIG_DIR / "insights_token"
INSIGHTS_LOGIN_CONFIG = CONFIG_DIR / "insights_login_config"

INSIGHTS_ENCRYPTION = DATA_DIR / "insights_encryption"

CONFIG_HOST_KEY = "host"
CONFIG_PORT_KEY = "port"
CONFIG_USE_HTTP = "use_http"
CONFIG_SSL_VERIFY = "ssl_verify"
CONFIG_REQUIRE_TOKEN = "require_token"

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

QPC_MIN_SERVER_VERSION = "1.4.0"

logging.captureWarnings(True)
logger = logging.getLogger(__name__)


def ensure_config_dir_exists():
    """Ensure the qpc configuration directory exists."""
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True)


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
    protocol = "https"
    if use_http:
        protocol = "http"

    server_location = (
        f"{protocol}://{config[CONFIG_HOST_KEY]}:{config[CONFIG_PORT_KEY]}"
    )
    return server_location


def read_client_token():
    """Retrieve client token for sonar server.

    :returns: The client token or None
    """
    if not QPC_CLIENT_TOKEN.exists():
        return None

    try:
        token_json = json.loads(QPC_CLIENT_TOKEN.read_text())
        return token_json.get("token")
    except json.decoder.JSONDecodeError:
        return None


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
    if not INSIGHTS_CONFIG.exists():
        return DEFAULT_INSIGHTS_CONFIG

    try:
        config = json.loads(INSIGHTS_CONFIG.read_text())
    except json.decoder.JSONDecodeError:
        return DEFAULT_INSIGHTS_CONFIG
    insights_config = dict(DEFAULT_INSIGHTS_CONFIG, **config)
    return insights_config


def read_server_config():  # noqa: C901 PLR0911
    """Retrieve configuration for sonar server.

    :returns: The validate dictionary with configuration
    """
    if not QPC_SERVER_CONFIG.exists():
        logger.error("Server config %s was not found.", QPC_SERVER_CONFIG)
        return None

    try:
        config = json.loads(QPC_SERVER_CONFIG.read_text())
    except json.decoder.JSONDecodeError:
        return None

    host = config.get(CONFIG_HOST_KEY)
    port = config.get(CONFIG_PORT_KEY)
    use_http = config.get(CONFIG_USE_HTTP)
    ssl_verify = config.get(CONFIG_SSL_VERIFY, False)
    require_token = config.get(CONFIG_REQUIRE_TOKEN)

    host_empty = host is None or host == ""
    port_empty = port is None or port == ""

    if host_empty or port_empty:
        return None

    if not isinstance(host, str):
        logger.error(
            "Server config %s has invalid value for host %s",
            QPC_SERVER_CONFIG,
            host,
        )
        return None

    if not isinstance(port, int):
        logger.error(
            "Server config %s has invalid value for port %s",
            QPC_SERVER_CONFIG,
            port,
        )
        return None

    if use_http is None:
        use_http = True

    if require_token is None:
        require_token = True

    if not isinstance(use_http, bool):
        logger.error(
            "Server config %s has invalid value for use_http %s",
            QPC_SERVER_CONFIG,
            use_http,
        )
        return None

    if not isinstance(require_token, bool):
        logger.error(
            "Server config %s has invalid value for require_token %s",
            QPC_SERVER_CONFIG,
            require_token,
        )
        return None

    if (
        ssl_verify is not None
        and not isinstance(ssl_verify, bool)
        and not isinstance(ssl_verify, str)
    ):
        logger.error(
            "Server config %s has invalid value for ssl_verify %s",
            QPC_SERVER_CONFIG,
            ssl_verify,
        )
        return None

    if (
        ssl_verify is not None
        and isinstance(ssl_verify, str)
        and not Path(ssl_verify).exists()
    ):
        logger.error(
            "Server config %s has invalid path for ssl_verify %s",
            QPC_SERVER_CONFIG,
            ssl_verify,
        )
        return None

    return {
        CONFIG_HOST_KEY: host,
        CONFIG_PORT_KEY: port,
        CONFIG_USE_HTTP: use_http,
        CONFIG_SSL_VERIFY: ssl_verify,
        CONFIG_REQUIRE_TOKEN: require_token,
    }


def write_config(config_file_path, config_dict):
    """Write configuration to config file.

    :param config_dict: dict containing configuration info
    :param config_file_path: path to configuration file
    """
    ensure_config_dir_exists()

    with Path(config_file_path).open("w", encoding="utf-8") as config_file:
        json.dump(config_dict, config_file, indent=4)


def write_server_config(server_config):
    """Write server configuration to server.config.

    :param server_config: dict containing server configuration
    """
    write_config(QPC_SERVER_CONFIG, server_config)


def write_insights_authentication(insights_authentication):
    """Write insights user authentication.

    :param insights_authentication: dict containing insights user token
    """
    write_config(INSIGHTS_LOGIN_CONFIG, insights_authentication)


def write_insights_login_config(login_config):
    """Write insights login configuration to insights_login_config.

    :param login_config: dict containing insights login configuration
    """
    encrypted_password = encrypt_password(login_config["password"])
    login_config["password"] = encrypted_password
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
    if not INSIGHTS_LOGIN_CONFIG.exists():
        raise QPCLoginConfigError("Insights login config was not found.")

    try:
        config = json.loads(INSIGHTS_LOGIN_CONFIG.read_text())
    except json.decoder.JSONDecodeError as exc:
        raise QPCLoginConfigError(
            f"Unable to load {INSIGHTS_LOGIN_CONFIG} file."
        ) from exc

    username = config[INSIGHTS_CONFIG_USERNAME_KEY]
    encrypted_password = config[INSIGHTS_CONFIG_PASSWORD_KEY]
    password = decrypt_password(encrypted_password)

    return {
        INSIGHTS_CONFIG_USERNAME_KEY: username,
        INSIGHTS_CONFIG_PASSWORD_KEY: password,
    }


def clear_insights_auth_token():
    """Delete the insights authentication token."""
    ensure_config_dir_exists()
    Path(INSIGHTS_AUTH_TOKEN).unlink(missing_ok=True)


def read_insights_auth_token():
    """Retrieve the insights authentication token.

    :returns: The Insight's user JWT auth token
    """
    if not INSIGHTS_AUTH_TOKEN.exists():
        return None

    return decrypt_password(INSIGHTS_AUTH_TOKEN.read_text())


def write_insights_auth_token(insights_auth_token):
    """Write insights user authentication.

    :param insights_auth_token: Insight's user JWT auth token
    """
    ensure_config_dir_exists()

    if insights_auth_token:
        with Path(INSIGHTS_AUTH_TOKEN).open("w", encoding="utf-8") as auth_token_file:
            os.write(auth_token_file, encrypt_password(insights_auth_token))
    else:
        clear_insights_auth_token()


def write_client_token(client_token):
    """Write client token to file client_token.

    :param client_token: dict containing client_token
    """
    ensure_config_dir_exists()

    with QPC_CLIENT_TOKEN.open("w", encoding="utf-8") as config_file:
        json.dump(client_token, config_file)


def delete_client_token():
    """Remove file client_token."""
    ensure_config_dir_exists()
    try:
        QPC_CLIENT_TOKEN.unlink()
    except FileNotFoundError:
        pass


def ensure_data_dir_exists():
    """Ensure the qpc data directory exists."""
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)


def setup_logging(verbosity):
    """Set up Python logging for qpc.

    Must be run after ensure_data_dir_exists().

    :param verbosity: verbosity level, as measured in -v's on the command line.
        Should be an integer.
    """
    # using default dict so any value (supposedly) higher than 1 will map to DEBUG
    # e.g calling qpc -vv would be the same as qpc -vvvvvvvvvvv
    verbosity_map = defaultdict(
        lambda: logging.DEBUG,
        {0: logging.ERROR, 1: logging.INFO},
    )
    log_level = verbosity_map[verbosity]
    log_prefix = "%(asctime)s - %(name)s - %(levelname)s"
    if log_level == logging.DEBUG:
        log_prefix += " - [%(funcName)s] - %(pathname)s:%(lineno)d"

    log_fmt = f"{log_prefix} - %(message)s"
    # Using basicConfig here means that all log messages, even
    # those not coming from qpc, will go to the log file
    logging.basicConfig(filename=QPC_LOG, format=log_fmt, level=log_level)
    stream_handler = logging.StreamHandler()
    if log_level == logging.DEBUG:
        # changing log format was breaking camayoc tests. let's add this extra logging
        # information only when the user actually requests for more logs.
        # (at least until we add an option controlling the log format)
        stream_handler.setFormatter(logging.Formatter(log_fmt))
    stream_handler.setLevel(log_level)
    main_package_name, *_ = __name__.partition(".")
    global_logger = logging.getLogger(main_package_name)
    global_logger.addHandler(stream_handler)


def log_request_info(method, command, url, response_json, response_code):
    """Log the information regarding the request being made.

    :param method: the method being called (ie. POST)
    :param command: the command being used (ie. qpc cred add)
    :param url: the server, port, and path
    (i.e. http://127.0.0.1:8000/api/v1/credentials/1)
    :param response_json: the response returned from the request
    :param response_code: the status code being returned (ie. 200)
    """
    message = 'Method: "%s", Command: "%s", URL: "%s", Response: "%s", Status Code: "%s'
    logger.debug(message, method, command, url, response_json, response_code)


def log_args(args):
    """Log the arguments for each qpc command.

    :param args: the arguments provided to the qpc command
    """
    message = 'Args: "%s"'
    logger.debug(message, args)


def handle_error_response(response):  # noqa: C901 PLR0912
    """Print errors from response data.

    :param response: The response object with a dictionary of keys and
        lists of errors
    """
    try:
        response_data = response.json()
        if isinstance(response_data, str):
            logger.error("Error: %s", str(response_data))
        if isinstance(response_data, dict):
            for err_key, err_cases in response_data.items():
                error_context = "Error"
                if err_key not in ["non_field_errors", "detail", "options"]:
                    error_context = err_key
                if isinstance(err_cases, str):
                    logger.error("%s: %s", error_context, err_cases)
                elif isinstance(err_cases, dict):
                    logger.error("%s: %s", error_context, err_cases)
                else:
                    for err_msg in err_cases:
                        logger.error("%s: %s", error_context, err_msg)
        elif isinstance(response_data, list):
            for err in response_data:
                logger.error("Error: %s", err)
        else:
            logger.error("Error: %s", str(response_data))
    except json.decoder.JSONDecodeError:
        pass


def pretty_print(json_data):
    """Provide pretty printing of output json data.

    :param json_data: the json data to pretty print
    :returns: the pretty print string of the json data
    """
    return json.dumps(json_data, sort_keys=True, indent=4, separators=(",", ": "))


# Read in a file and make it a list
def read_in_file(filename):
    """Read values from file into a list object. Expecting newline delimited.

    :param filename: the filename to read
    :returns: the list of values found in the file
    :raises: ValueError if incoming value is not a file that could be found
    """
    result = None
    input_path = Path(os.path.expandvars(filename)).expanduser()
    if input_path.is_file():
        try:
            with input_path.open("r", encoding="utf-8") as in_file:
                result = in_file.read().splitlines()
        except EnvironmentError as err:
            logger.error(
                t(messages.READ_FILE_ERROR), {"path": input_path, "error": err}
            )
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
    input_path = Path(os.path.expandvars(filename)).expanduser()
    if not input_path:
        raise ValueError(t(messages.REPORT_OUTPUT_CANNOT_BE_EMPTY % param_name))
    if input_path.is_dir():
        raise ValueError(
            t(messages.REPORT_OUTPUT_IS_A_DIRECTORY % (param_name, input_path))
        )
    directory = input_path.absolute().parent
    if not directory.exists():
        raise ValueError(t(messages.REPORT_DIRECTORY_DOES_NOT_EXIST % directory))


def write_file(filename, content, binary=False):
    """Write content to a file.

    :param filename: the filename to write
    :param content: the file content to write
    :raises: EnvironmentError if file cannot be written
    """
    result = None
    if filename is None:
        print(content)
    else:
        input_path = Path(os.path.expandvars(filename)).expanduser()
        mode = "w"
        if binary:
            mode = "wb"
        with input_path.open(mode) as out_file:
            out_file.write(content)
    return result


def extract_json_from_tar(fileobj_content, print_pretty=True):
    """Extract json data from tar.gz bytes.

    :param fileobj_content: BytesIo object with tarball of json dict
    :param print_pretty: Boolean to determine whether to return pretty
        print json (str) or normal json
    """
    with tarfile.open(fileobj=io.BytesIO(fileobj_content), mode="r:gz") as tar:
        json_file = tar.getmembers()[0]
        tar_info = tar.extractfile(json_file)
        json_data = json.loads(tar_info.read().decode("utf-8"))
        if print_pretty:
            return pretty_print(json_data)
        return json_data


def create_tar_buffer(files_data):
    """Generate a file buffer based off a dictionary."""
    if not isinstance(files_data, (dict,)):
        logger.error(messages.CREATE_TAR_ERROR_FILE)
        return None
    if not all(isinstance(v, (str, dict)) for v in files_data.values()):
        logger.error(messages.CREATE_TAR_ERROR_INCORRECT_STRUCTURE)
        return None
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar_file:
        for file_name, file_content in files_data.items():
            if file_name.endswith("json"):
                file_buffer = io.BytesIO(json.dumps(file_content).encode("utf-8"))
            elif file_name.endswith("csv"):
                file_buffer = io.BytesIO(file_content.encode("utf-8"))
            else:
                logger.error(messages.UNKNOWN_FILE_EXTENSION)
                return None
            info = tarfile.TarInfo(name=file_name)
            info.size = len(file_buffer.getvalue())
            tar_file.addfile(tarinfo=info, fileobj=file_buffer)
    tar_buffer.seek(0)
    return tar_buffer.getvalue()


def check_extension(extension, path):
    """Check if .json is in the file extension."""
    if path is None:
        return
    if extension not in path:
        logger.error(t(messages.OUTPUT_FILE_TYPE), extension)
        sys.exit(1)


def write_encryption_key_if_non_existent():
    """Generate encryption key.

    Key will be generated only once and saved at INSIGHTS_ENCRYPTION file,
    the function will check its existence every time it is called
    """
    if not INSIGHTS_ENCRYPTION.exists():
        key = Fernet.generate_key()
        INSIGHTS_ENCRYPTION.write_bytes(key)
        INSIGHTS_ENCRYPTION.chmod(0o600)


def load_encryption_key():
    """Load encryption from insights_encryption file."""
    stats = INSIGHTS_ENCRYPTION.stat()
    if oct(stats.st_mode).endswith("00"):
        return INSIGHTS_ENCRYPTION.read_bytes()

    raise QPCEncryptionKeyError(
        "There was a problem while trying to load the password encryption key."
    )


def encrypt_password(password):
    """Encrypt password before saving it to a config file."""
    write_encryption_key_if_non_existent()
    key = load_encryption_key()

    encryption_algorithm = Fernet(key)

    encrypted_password = encryption_algorithm.encrypt(password.encode())
    return encrypted_password.decode()


def decrypt_password(password):
    """Retrieve password from login config file and decrypt it."""
    key = load_encryption_key()
    encryption_algorithm = Fernet(key)

    try:
        decrypted_password = encryption_algorithm.decrypt(password.encode())
    except InvalidToken as exc:
        raise QPCEncryptionKeyError(
            "There was a problem while decrypting your password."
        ) from exc
    return decrypted_password.decode()


def check_if_prompt_is_not_empty(pass_prompt):
    """Validate user prompt."""
    if not pass_prompt:
        logger.error(t(messages.PROMPT_INPUT))
        raise SystemExit(2)
