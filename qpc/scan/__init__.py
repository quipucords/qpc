"""Constants for the Scan commands."""

SUBCOMMAND = "scan"
ADD = "add"
EDIT = "edit"
START = "start"
LIST = "list"
JOB = "job"
SHOW = "show"
CANCEL = "cancel"
CLEAR = "clear"

# Status values
SCAN_STATUS_CREATED = "created"
SCAN_STATUS_PENDING = "pending"
SCAN_STATUS_RUNNING = "running"
SCAN_STATUS_PAUSED = "paused"
SCAN_STATUS_CANCELED = "canceled"
SCAN_STATUS_COMPLETED = "completed"
SCAN_STATUS_FAILED = "failed"


SCAN_URI = "/api/v1/scans/"
SCAN_BULK_DELETE_URI = "/api/v1/scans/bulk_delete/"
SCAN_JOB_V1_URI = "/api/v1/jobs/"
SCAN_JOB_URI = "/api/v2/jobs/"

SCAN_TYPE_CONNECT = "connect"
SCAN_TYPE_INSPECT = "inspect"

JBOSS_EAP = "jboss_eap"
JBOSS_FUSE = "jboss_fuse"
JBOSS_WS = "jboss_ws"
OPTIONAL_PRODUCTS = [JBOSS_EAP, JBOSS_FUSE, JBOSS_WS]
