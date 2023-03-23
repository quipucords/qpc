"""Constants for the Credential commands."""

SUBCOMMAND = "cred"
ADD = "add"
LIST = "list"
EDIT = "edit"
SHOW = "show"
CLEAR = "clear"


NETWORK_CRED_TYPE = "network"
VCENTER_CRED_TYPE = "vcenter"
SATELLITE_CRED_TYPE = "satellite"
OPENSHIFT_CRED_TYPE = "openshift"

BECOME_SUDO = "sudo"
BECOME_SU = "su"
BECOME_PBRUN = "pbrun"
BECOME_PFEXEC = "pfexec"
BECOME_DOAS = "doas"
BECOME_DZDO = "dzdo"
BECOME_KSU = "ksu"
BECOME_RUNAS = "runas"

BECOME_CHOICES = [
    BECOME_SUDO,
    BECOME_SU,
    BECOME_PBRUN,
    BECOME_PFEXEC,
    BECOME_DOAS,
    BECOME_DZDO,
    BECOME_KSU,
    BECOME_RUNAS,
]

CREDENTIAL_URI = "/api/v1/credentials/"
