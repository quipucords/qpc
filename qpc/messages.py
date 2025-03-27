"""CLI messages for translation."""

from qpc.source import SOURCE_TYPE_CHOICES

VALID_DATA_SOURCES = ", ".join(SOURCE_TYPE_CHOICES)

CRED_NAME_HELP = "Credential name."
CRED_TYPE_HELP = f"Type of credential. Valid values: {VALID_DATA_SOURCES}."
CRED_TYPE_FILTER_HELP = (
    f"Filter for listing credentials by type. Valid values: {VALID_DATA_SOURCES}."
)
CRED_USER_HELP = "User name for authenticating against the target system."
CRED_PWD_HELP = "Password for authenticating against the target system."
CRED_SSH_FILE_HELP = "File that contains the SSH key."
CRED_SSH_KEY_HELP = "The SSH Private Key."
CRED_SSH_PSPH_HELP = "SSH passphrase for authenticating against the target system."
CRED_CLEAR_ALL_HELP = "Remove all credentials."

CRED_ADDED = 'Credential "%s" was added.'

CRED_REMOVED = 'Credential "%s" was removed.'
CRED_FAILED_TO_REMOVE = (
    'Failed to remove credential "%s". For more information, see the server log file.'
)
CRED_CLEAR_ALL_SKIPPED_ASSIGNED_TO_SOURCE = (
    "Could not delete credential ID %(credential_id)s "
    "because it is assigned to at least one source "
    "(source ID %(source_ids)s)."
)
CRED_CLEAR_ALL_SUMMARY = (
    "Successfully deleted %(deleted_count)s credentials. "
    "%(skipped_count)s credentials could not be deleted."
)
CRED_NOT_FOUND = 'Credential "%s" was not found.'
CRED_NO_CREDS_TO_REMOVE = "No credentials exist to be removed."

CRED_EDIT_NO_ARGS = 'No arguments were provided to edit credential "%s".'
CRED_DOES_NOT_EXIST = 'Credential "%s" does not exist.'
CRED_UPDATED = 'Credential "%s" was updated.'

CRED_LIST_NO_CREDS = "No credentials exist yet."

CRED_BECOME_METHOD_HELP = (
    "The method to become for network privilege "
    "escalation. Valid values: sudo, su, pbrun, pfexec, doas, dzdo, "
    "ksu, runas."
)
CRED_BECOME_USER_HELP = (
    "The user to become when running a privileged command during network scan."
)
CRED_BECOME_PASSWORD_HELP = (
    "The privilege escalation password to be used when running a network scan."
)
CRED_TOKEN_HELP = "Authentication token."

SOURCE_NAME_HELP = "Source name."
SOURCES_NAME_HELP = "List of source names."
SOURCE_TYPE_HELP = f"Type of source. Valid values: {VALID_DATA_SOURCES}."
SOURCE_HOSTS_HELP = (
    'IP ranges to scan. Run the "man %s" command for more '
    "information about supported formats."
)
SOURCE_EXCLUDE_HOSTS_HELP = (
    "IP ranges to exclude from scan. Only supported "
    'for network sources. Run the "man %s" command for more information '
    "about supported formats."
)
SOURCE_CREDS_HELP = "Credentials to associate with a source."
SOURCE_PORT_HELP = (
    "Port to use for connection for the scan; "
    "network default is 22, vcenter default is 443."
)
SOURCE_PARAMIKO_HELP = (
    "Set Ansible connection method to paramiko. default connection method is ssh."
)
SOURCE_SSL_CERT_HELP = (
    "If true, the SSL certificate will"
    " be verified when making requests to the source, otherwise no "
    "verification will occur. "
    "Not valid for network sources."
)
SOURCE_SSL_PROTOCOL_HELP = (
    "The SSL protocol to be used during a secure"
    " connection. "
    "Not valid for network sources."
)
SOURCE_SSL_DISABLE_HELP = (
    "Disable SSL usage during a connection. Not valid for network sources."
)
SOURCE_ADD_CREDS_NOT_FOUND = (
    "An error occurred while processing the "
    '"--cred" input values. References for the following credential '
    'could not be found: %(reference)s. Failed to add source "%(source)s". '
    "For more information, see the server log file."
)
SOURCE_ADD_CRED_PROCESS_ERR = (
    "An error occurred while processing the "
    '"--cred" input values. Failed to add source "%s". For more '
    "information, see the server log file."
)
SOURCE_ADDED = 'Source "%s" was added.'

SOURCE_CLEAR_ALL_HELP = "Remove all sources."
SOURCE_REMOVED = 'Source "%s" was removed.'
SOURCE_FAILED_TO_REMOVE = 'Failed to remove source "%s".'
SOURCE_NOT_FOUND = 'Source "%s" was not found.'
SOURCE_NO_SOURCES_TO_REMOVE = "No sources exist to be removed."
SOURCE_CLEAR_ALL_SKIPPED_ASSIGNED_TO_SCAN = (
    "Could not delete source ID %(source_id)s "
    "because it is assigned to at least one scan "
    "(scan ID %(scan_ids)s)."
)
SOURCE_CLEAR_ALL_SUMMARY = (
    "Successfully deleted %(deleted_count)s sources. "
    "%(skipped_count)s sources could not be deleted."
)
SOURCE_EDIT_NO_ARGS = "No arguments were provided to edit source %s."
SOURCE_DOES_NOT_EXIST = 'Source "%s" does not exist.'

SOURCE_EDIT_CREDS_NOT_FOUND = (
    "An error occurred while processing the "
    '"--cred" input values. References for the following credential '
    'could not be found: %(reference)s. Failed to edit source "%(source)s". For more '
    "information, see the server log file."
)
SOURCE_EDIT_CRED_PROCESS_ERR = (
    "An error occurred while processing the "
    '"--cred" input values. Failed to edit source "%s". For more '
    "information, see the server log file."
)
SOURCE_UPDATED = 'Source "%s" was updated.'
SOURCE_LIST_NO_SOURCES = "No sources exist yet."
SOURCE_TYPE_FILTER_HELP = (
    "Filter for listing sources by type. Valid values: vcenter, network."
)


SCAN_NAME_HELP = "Scan name."
SCAN_ADDED = 'Scan "%s" was added.'
SCAN_UPDATED = 'Scan "%s" was updated.'
SCAN_JOB_ID_HELP = "Scan job identifier."
SCAN_TYPE_FILTER_HELP = (
    "Filter for listing scan jobs by type. Valid values: connect, inspect."
)
SCAN_STATUS_FILTER_HELP = (
    "Filter for listing scan jobs by status. Valid "
    "values: created, pending, running, paused, canceled, completed, failed."
)
SCAN_MAX_CONCURRENCY_HELP = "Maximum number of concurrent scans; default is 25."
SCAN_DOES_NOT_EXIST = 'Scan "%s" does not exist.'
SCAN_LIST_NO_SCANS = "No scans found."
SCAN_STARTED = 'Scan "%s" started.'
SCAN_CANCELED = 'Scan "%s" canceled.'
SCAN_CLEAR_ALL_HELP = "Remove all scans."
SCAN_REMOVED = 'Scan "%s" was removed.'
SCAN_FAILED_TO_REMOVE = 'Failed to remove scan "%s".'
SCAN_NOT_FOUND = 'Scan "%s" was not found.'
SCAN_NO_SCANS_TO_REMOVE = "No scans exist to be removed."
SCAN_CLEAR_ALL_SUMMARY = "Successfully deleted %(deleted_count)s scans."
SCAN_EDIT_NO_ARGS = "No arguments were provided to edit scan %s."
SCAN_JOB_ID_STATUS = (
    'Provide the "--status" filter with a scan name to '
    "filter the list of related scan jobs."
)
SCAN_ENABLED_PRODUCT_HELP = (
    "Contains the list of products to include for extended product search. "
    "Valid values: jboss_eap, jboss_fuse, jboss_ws."
)
SCAN_EXT_SEARCH_DIRS_HELP = (
    "A list of fully-qualified paths to search for extended product search."
)
REPORT_JSON_FILE_HELP = (
    "A list of files that contain the json details reports to merge."
)
REPORT_JSON_DIR_HELP = (
    "The path to a directory that contain files of json details reports to merge"
)
REPORT_JSON_FILES_HELP = "At least two json details report files are required to merge."
REPORT_MISSING_REPORT_VERSION = (
    "WARNING: "
    "The file %s is missing report_version.  "
    "Future releases will not tolerate a missing or invalid report_version."
)
REPORT_INVALID_REPORT_TYPE = (
    "The file %(file)s contains invalid report type %(report_type)s."
)
REPORT_JSON_DIR_NO_FILES = "No files with extension .json found in %s."
REPORT_VALIDATE_JSON = "Checking files for valid json details report. %s"
REPORT_JSON_MISSING_ATTR = (
    "Failed: %(file)s is not a details report. Missing %(key)s. Excluding from merge."
)
REPORT_JSON_DIR_FILE_SUCCESS = "Success: %s is a valid details report."
REPORT_JSON_DIR_ALL_FAIL = "No details reports were found."
REPORTS_REPORTS_DO_NOT_EXIST = "The following scan jobs did not produce reports: %s."
REPORT_SCAN_JOB_ID_HELP = "Scan job identifier."
REPORT_REPORT_ID_HELP = "Report identifier."
REPORT_REPORT_IDS_HELP = "Report identifiers."
REPORT_SCAN_JOB_IDS_HELP = "Scan job identifiers."
REPORT_OUTPUT_JSON_HELP = "Output as a JSON file."
REPORT_OUTPUT_CSV_HELP = "Output as a CSV file."
REPORT_PATH_HELP = "Output file location."
REPORT_SJ_DOES_NOT_EXIST = "Scan Job %s does not exist."
REPORT_SJS_DO_NOT_EXIST = "The following scan jobs do not exist: %s."
REPORT_NO_AGGREGATE_REPORT_FOR_SJ = "No aggregate report available for scan job %s."
REPORT_NO_AGGREGATE_REPORT_FOR_REPORT_ID = "The aggregate report %s does not exist."
REPORT_NO_DEPLOYMENTS_REPORT_FOR_SJ = "No deployments report available for scan job %s."
REPORT_NO_DEPLOYMENTS_REPORT_FOR_REPORT_ID = "The deployments report %s does not exist."
REPORT_NO_DETAIL_REPORT_FOR_SJ = "No report detail available for scan job %s."
REPORT_NO_DETAIL_REPORT_FOR_REPORT_ID = "No report detail available for report id %s."
REPORT_NO_INSIGHTS_REPORT_FOR_SJ = "No Insights report available for scan job %s."
REPORT_NO_INSIGHTS_REPORT_FOR_REPORT_ID = "Insights report %s does not exist."
REPORT_NO_INSIGHTS_CLARIFICATION = (
    "The Insights report can only be generated if at least one source type is "
    "network, satellite, or vcenter."
)
REPORT_OUTPUT_CANNOT_BE_EMPTY = "%s cannot be empty string."
REPORT_OUTPUT_IS_A_DIRECTORY = "%s %s was a directory."
REPORT_DIRECTORY_DOES_NOT_EXIST = "The directory %s does not exist.  Cannot write here."
REPORT_JSON_DIR_NOT_FOUND = "%s is not a directory"
REPORT_SUCCESSFULLY_WRITTEN = "Report written successfully."
REPORT_SUCCESSFULLY_MERGED = (
    "Report merge job %(id)s created. "
    'To check processing status, run "%(prog_name)s scan job --id %(id)s"'
)
REPORT_UPLOAD_VALIDATE_JSON = "Checking file for valid JSON details report. %s"
REPORT_UPLOAD_FILE_INVALID_JSON = "Failed: %s is not a JSON details report."
REPORT_UPLOAD_JSON_FILE_HELP = "The path to the details report JSON file."
REPORT_UPLOAD_VALIDATE_JSON = "Checking %s for valid JSON details report."
REPORT_SUCCESSFULLY_UPLOADED = (
    "Report uploaded. Job %(id)s created. "
    'To check processing status, run "%(prog_name)s scan job --id %(id)s"'
)
REPORT_FAILED_TO_UPLOADED = "Report could not be created.  Error: %s"
DISABLE_OPT_PRODUCTS_HELP = (
    "The product inspection exclusions. "
    "Contains the list of products to exclude from inspection. "
    "Valid values: jboss_eap, jboss_fuse, jboss_ws."
)

VERBOSITY_HELP = "Verbose mode. Use up to -vvvv for more verbosity."


CONNECTION_ERROR_MSG = (
    "A connection error occurred while attempting to "
    "communicate with the server. The server has been "
    'configured to be contacted via "%(protocol)s" at host "%(host)s" '
    'with port "%(port)s" but is not responding.'
)

READ_FILE_ERROR = "Error reading from %(path)s: %(error)s."
WRITE_FILE_ERROR = "Error writing to %(path)s: %(error)s."
NOT_A_FILE = "Input %s was not a file."
FILE_NOT_FOUND = "Input %s was not found."

PROMPT_INPUT = "Provide a valid input."
PASSWORD_PROMPT_WITH_NO_TTY = (
    "Cannot prompt for password, sshpassphrase, become_password"
    " or auth_token if not connected to a tty."
)
CONN_PASSWORD = "Provide a connection password."
SSH_PASSPHRASE = "Provide a passphrase for the SSH Key."
SSH_KEY = "Provide a Private SSH Key followed by a Control-D."
SSH_KEY_PROMPT = "Private SSH Key: "
BECOME_PASSWORD = (
    "Provide a privilege escalation password to be used when running a network scan."
)
AUTH_TOKEN = "Provide a token for authentication.\nToken: "

MERGE_ERROR = "No reports found. Error json: %s"
SERVER_CONFIG_REQUIRED = (
    "Configure server using command below: \n$ %s server config --host HOST --port PORT"
)
SERVER_LOGIN_REQUIRED = "Log in using the command below: \n$ %s server login"
SERVER_CONFIG_HOST_HELP = "Host or IP address for the server."
SERVER_CONFIG_PORT_HELP = "Port number for the server; the default is 9443."
SERVER_CONFIG_SSL_CERT_HELP = (
    "File path to the SSL certificate to use for verification."
)
SERVER_CONFIG_SUCCESS = (
    "Server connectivity was successfully configured. "
    'The server will be contacted via "%(protocol)s" at host "%(host)s"'
    ' with port "%(port)s".'
)
SERVER_INTERNAL_ERROR = (
    "An internal server error occurred. For more information, see the server log file."
)
SERVER_STATUS_FAILURE = (
    "Unexpected failure occurred when accessing the status endpoint."
)
STATUS_PATH_HELP = "Output file location."
STATUS_SUCCESSFULLY_WRITTEN = "Server status written successfully."

LOGIN_USER_HELP = (
    "The user name to log in to the server. If not provided, user will be prompted."
)
LOGIN_PASS_HELP = (
    "The password to log in to the server. If not provided, user will be prompted."
)
LOGIN_USERNAME_PROMPT = "User name: "
LOGIN_SUCCESS = "Login successful."

LOGOUT_SUCCESS = "Logged out."

INSIGHTS_NOT_LOGGED_IN = "Must first login to authenticate"
INSIGHTS_TOKEN_EXPIRED = "Authorization token expired, please re-login to Insights"
INSIGHTS_TOKEN_CORRUPT = "Corrupt Authorization token, please re-login to Insights"
INSIGHTS_TOKEN_INVALID = "Invalid Authorization token, please re-login to Insights"
INSIGHTS_SSO_CONFIG_QUERY = "Querying Insights SSO configuration at %s for %s"
INSIGHTS_SSO_QUERY_FAILED = "Failed to query the Insights SSO configuration: missing %s"
INSIGHTS_AUTH_ERROR = "Authorization failed, please re-login to Insights"
INSIGHTS_LOGIN_REQUEST = "Requesting Login authorization from %s"
INSIGHTS_LOGIN_REQUEST_FAILED = "Failed to request login authorization: %s"
INSIGHTS_LOGIN_VERIFYING = "Verifying Login authorization at %s"
INSIGHTS_LOGIN_VERIFICATION_FAILED = "Failed to verify Login authorization: %s"
INSIGHTS_LOGIN_VERIFICATION_TIMEOUT = "Time-out while waiting for Login authorization"
INSIGHTS_INPUT_GZIP_HELP = "Path to local tar.gz file containing an Insights report."
INSIGHTS_LOCAL_REPORT_NOT = "%s file cannot be found."
INSIGHTS_LOCAL_REPORT_NOT_TAR_GZ = "%s file is not a tar.gz."
DOWNLOAD_NO_REPORT_FOR_SJ = "No reports available for scan job %s."
DOWNLOAD_NO_REPORT_FOUND = "Report %s not found."
DOWNLOAD_PATH_HELP = (
    "The output file's name and location. This file is required to be a tar.gz"
)
DOWNLOAD_SUCCESSFULLY_WRITTEN = "Report %(report)s successfully written to %(path)s."
DOWNLOAD_SJ_DOES_NOT_EXIST = "Scan Job %s does not exist."

SERVER_TOO_OLD_FOR_CLI = (
    "The CLI requires a minimum server version of %(min_version)s.  "
    "Upgrade your server to %(min_version)s or greater.  "
    "Server is currently at version %(current_version)s."
)
OUTPUT_FILE_TYPE = "The output file's extension is required to be %s."
INSIGHTS_CONFIG_HOST_HELP = "Host or IP address."
INSIGHTS_CONFIG_PORT_HELP = "Port number."
INSIGHTS_CONFIG_SUCCESS = (
    "Insights configuration was successfully added. Captured values: %s"
)
INSIGHTS_CONFIG_SSO_HOST_HELP = "Insights SSO Host"
INSIGHTS_PUBLISH_REPORT = "Publishing report to Insights at %s"
INSIGHTS_PUBLISH_FAILED = "Failed to publish the report to Insights: %s"
INSIGHTS_PUBLISH_SUCCESSFUL = "The report was successfully published."
INSIGHTS_PUBLISH_INTERNAL_SERVER_ERROR = (
    "The server encountered an unexpected condition"
    " that prevented it from fulfilling the request."
)
INSIGHTS_PUBLISH_NOT_FOUND_ERROR = (
    "The server is either unavailable or the page couldn't be found."
    " Check your insights configuration."
)
INSIGHTS_PUBLISH_RESPONSE = "Response from insights: %s"
INSIGHTS_RESPONSE = "Response from %s: %s"

_INVALID_PREFIX = "Payload file is not valid, due to:"
INSIGHTS_REPORT_CONTENT_MIN_NUMBER = (
    f"{_INVALID_PREFIX} Insights report should contain at least 2 files."
)
INSIGHTS_REPORT_CONTENT_MISSING_METADATA = (
    f"{_INVALID_PREFIX} Insights report is missing metadata.json file."
)
INSIGHTS_REPORT_CONTENT_NOT_JSON = (
    f"{_INVALID_PREFIX} Insights report should contain only json files."
)
INSIGHTS_REPORT_CONTENT_UNEXPECTED = (
    f"{_INVALID_PREFIX} Insights report tarball contains an unexpected file structure."
)
INSIGHTS_REPORT_DOWNLOAD_SUCCESSFUL = "The report was successfully downloaded."

CREATE_TAR_ERROR_FILE = "ERROR: files_data is not a dict"
CREATE_TAR_ERROR_INCORRECT_STRUCTURE = "ERROR: Not correct structure for tar"
UNKNOWN_FILE_EXTENSION = "ERROR: unknown file extension"
